/* ============================================================
   Granas Module — Platform JavaScript
   Navigation, Simulator, Blueprint Canvas, Particles
   21 × 34 cm Production Module — PRIMEnergeia S.A.S.
   ============================================================ */

// ── Page Navigation ──────────────────────────────────────
function showPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-' + pageId).classList.add('active');

  document.querySelectorAll('.navbar-links a[data-page]').forEach(a => {
    a.classList.toggle('active', a.dataset.page === pageId);
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Close mobile menu
  const links = document.getElementById('navLinks');
  if (links) links.classList.remove('open');

  // Draw blueprint if navigating to that page
  if (pageId === 'blueprint') {
    setTimeout(drawBlueprint, 100);
  }
}

function toggleMobile() {
  const links = document.getElementById('navLinks');
  if (links) links.classList.toggle('open');
}

// ── Hero Particles ───────────────────────────────────────
function initParticles() {
  const container = document.getElementById('particles');
  if (!container) return;

  for (let i = 0; i < 50; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    p.style.left = Math.random() * 100 + '%';
    p.style.animationDuration = (6 + Math.random() * 10) + 's';
    p.style.animationDelay = Math.random() * 8 + 's';
    p.style.width = (1 + Math.random() * 2) + 'px';
    p.style.height = p.style.width;

    // Mix emerald and gold particles
    if (Math.random() > 0.7) {
      p.style.background = '#fbc02d';
    }
    container.appendChild(p);
  }
}

// ── Module Power Simulator ───────────────────────────────
function updateSim() {
  const area = parseFloat(document.getElementById('slider-area').value);
  const pce  = parseFloat(document.getElementById('slider-pce').value);
  const jsc  = parseFloat(document.getElementById('slider-jsc').value);
  const irr  = parseFloat(document.getElementById('slider-irr').value);
  const cf   = parseFloat(document.getElementById('slider-cf').value) / 100;
  const eg   = parseFloat(document.getElementById('slider-eg').value) / 100;

  // Labels
  document.getElementById('val-area').textContent = area + ' cm²';
  document.getElementById('val-pce').textContent  = pce.toFixed(1) + '%';
  document.getElementById('val-jsc').textContent  = jsc.toFixed(1);
  document.getElementById('val-irr').textContent  = irr + ' W/m²';
  document.getElementById('val-cf').textContent   = cf.toFixed(2) + (cf >= 0.20 ? ' (MX)' : '');
  document.getElementById('val-eg').textContent   = eg.toFixed(2) + ' eV';

  // Physics calculations (same as granas_module.py)
  const area_m2 = area / 10000;
  const power   = (pce / 100) * area_m2 * irr;
  const voc     = eg * 0.75;
  const isc     = jsc * area / 1000;
  const ff      = (voc * isc > 0) ? Math.min(power / (voc * isc), 0.90) : 0;
  const annual  = power * cf * 8760 / 1000;

  // Update results
  document.getElementById('result-power').innerHTML  = power.toFixed(3) + '<span class="result-metric-unit"> W</span>';
  document.getElementById('result-voc').innerHTML    = voc.toFixed(3) + '<span class="result-metric-unit"> V</span>';
  document.getElementById('result-isc').innerHTML    = isc.toFixed(3) + '<span class="result-metric-unit"> A</span>';
  document.getElementById('result-ff').innerHTML     = ff.toFixed(3);
  document.getElementById('result-annual').innerHTML = annual.toFixed(3) + '<span class="result-metric-unit"> kWh</span>';
  document.getElementById('result-cf').innerHTML     = cf.toFixed(2) + '<span class="result-metric-unit">' + (cf >= 0.20 ? ' MX' : '') + '</span>';
}

// ── Blueprint Canvas — 21 × 34 cm Production Module ─────
// Faithful reproduction of the hand-drawn Granas Module blueprint
// Two columns (10.5 cm each) × 6 rows: V, 4×diamond, Λ
// ~9 cm triangle sides (top/bottom), ~7 cm diamond sides (middle)
function drawBlueprint() {
  const canvas = document.getElementById('blueprintCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const W = canvas.width;
  const H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const pad = 24;
  const drawW = W - 2 * pad;
  const drawH = H - 2 * pad;
  const sx = drawW / 21.0;
  const sy = drawH / 34.0;

  function px(x) { return pad + x * sx; }
  function py(y) { return pad + y * sy; }

  // ═══════════════════════════════════════════════════════
  //  21 × 34 cm GEOMETRY
  //  Y-divisions: 0, 7, 12, 17, 22, 27, 34
  //  Center vertical at x = 10.5
  //  Sub-center verticals at x = 5.25 and x = 15.75 (rows 2-5)
  // ═══════════════════════════════════════════════════════

  // Fill colors — alternating greens for segment differentiation
  const fills = [
    'rgba(0, 255, 213, 0.06)',
    'rgba(0, 255, 136, 0.05)',
    'rgba(0, 200, 160, 0.055)',
    'rgba(80, 255, 180, 0.05)',
    'rgba(0, 230, 190, 0.045)',
    'rgba(40, 255, 160, 0.055)',
  ];

  function fillPoly(points, fillIdx) {
    ctx.beginPath();
    ctx.moveTo(px(points[0][0]), py(points[0][1]));
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(px(points[i][0]), py(points[i][1]));
    }
    ctx.closePath();
    ctx.fillStyle = fills[fillIdx % fills.length];
    ctx.fill();
  }

  // Helper: draw X-pattern triangles in a rectangular cell
  function fillXCell(x0, y0, x1, y1, startFill) {
    const mx = (x0 + x1) / 2;
    const my = (y0 + y1) / 2;
    fillPoly([[x0,y0],[x1,y0],[mx,my]], startFill);      // top
    fillPoly([[x1,y0],[x1,y1],[mx,my]], startFill + 1);   // right
    fillPoly([[x1,y1],[x0,y1],[mx,my]], startFill + 2);   // bottom
    fillPoly([[x0,y1],[x0,y0],[mx,my]], startFill + 3);   // left
  }

  // Helper: draw V-pattern (top) in a column
  function fillVTop(x0, y0, x1, y1, startFill) {
    const mx = (x0 + x1) / 2;
    fillPoly([[x0,y0],[mx,y0],[mx,y1]], startFill);       // left triangle
    fillPoly([[mx,y0],[x1,y0],[mx,y1]], startFill + 1);   // right triangle
  }

  // Helper: draw Λ-pattern (bottom) in a column
  function fillVBot(x0, y0, x1, y1, startFill) {
    const mx = (x0 + x1) / 2;
    fillPoly([[x0,y1],[mx,y0],[x0,y0]], startFill);       // left triangle (note: y0 is apex)
    fillPoly([[x1,y1],[mx,y0],[x1,y0]], startFill + 1);   // right triangle
  }

  // ── ROW 1 (0→7): Top V triangles ──
  // Left column V
  fillVTop(0, 0, 10.5, 7, 0);
  // Right column V
  fillVTop(10.5, 0, 21, 7, 2);

  // ── ROW 2 (7→12): Diamond grid ──
  fillXCell(0, 7, 5.25, 12, 0);
  fillXCell(5.25, 7, 10.5, 12, 2);
  fillXCell(10.5, 7, 15.75, 12, 4);
  fillXCell(15.75, 7, 21, 12, 1);

  // ── ROW 3 (12→17): Diamond grid ──
  fillXCell(0, 12, 5.25, 17, 3);
  fillXCell(5.25, 12, 10.5, 17, 5);
  fillXCell(10.5, 12, 15.75, 17, 1);
  fillXCell(15.75, 12, 21, 17, 3);

  // ── ROW 4 (17→22): Diamond grid ──
  fillXCell(0, 17, 5.25, 22, 2);
  fillXCell(5.25, 17, 10.5, 22, 0);
  fillXCell(10.5, 17, 15.75, 22, 3);
  fillXCell(15.75, 17, 21, 22, 5);

  // ── ROW 5 (22→27): Diamond grid ──
  fillXCell(0, 22, 5.25, 27, 5);
  fillXCell(5.25, 22, 10.5, 27, 3);
  fillXCell(10.5, 22, 15.75, 27, 0);
  fillXCell(15.75, 22, 21, 27, 2);

  // ── ROW 6 (27→34): Bottom Λ triangles ──
  fillVBot(0, 27, 10.5, 34, 4);
  fillVBot(10.5, 27, 21, 34, 0);

  // ═══════════════════════════════════════════════════════
  //  CFRP SKELETON LINES
  // ═══════════════════════════════════════════════════════
  const cfrpColor = 'rgba(0, 255, 213, 0.55)';
  const cfrpWidth = 1.8;

  function edge(x1, y1, x2, y2) {
    ctx.beginPath();
    ctx.moveTo(px(x1), py(y1));
    ctx.lineTo(px(x2), py(y2));
    ctx.strokeStyle = cfrpColor;
    ctx.lineWidth = cfrpWidth;
    ctx.stroke();
  }

  // Panel border
  ctx.strokeStyle = 'rgba(0, 255, 213, 0.7)';
  ctx.lineWidth = 2.5;
  ctx.strokeRect(pad, pad, drawW, drawH);

  // ── Horizontal lines ──
  [7, 12, 17, 22, 27].forEach(y => edge(0, y, 21, y));

  // ── Center vertical (full height) ──
  edge(10.5, 0, 10.5, 34);

  // ── Sub-center verticals (rows 2-5 only) ──
  edge(5.25, 7, 5.25, 27);
  edge(15.75, 7, 15.75, 27);

  // ── Row 1: Top V diagonals ──
  // Left column
  edge(0, 0, 5.25, 7);
  edge(10.5, 0, 5.25, 7);
  // Right column
  edge(10.5, 0, 15.75, 7);
  edge(21, 0, 15.75, 7);

  // ── Rows 2-5: X diagonals in each sub-cell ──
  const yCells = [[7,12],[12,17],[17,22],[22,27]];
  const xCells = [[0,5.25],[5.25,10.5],[10.5,15.75],[15.75,21]];

  yCells.forEach(([y0, y1]) => {
    xCells.forEach(([x0, x1]) => {
      edge(x0, y0, x1, y1);  // diagonal ↘
      edge(x1, y0, x0, y1);  // diagonal ↙
    });
  });

  // ── Row 6: Bottom Λ diagonals ──
  // Left column
  edge(0, 34, 5.25, 27);
  edge(10.5, 34, 5.25, 27);
  // Right column
  edge(10.5, 34, 15.75, 27);
  edge(21, 34, 15.75, 27);

  // ═══════════════════════════════════════════════════════
  //  SEGMENT LABELS
  // ═══════════════════════════════════════════════════════
  ctx.font = 'bold 10px "JetBrains Mono", monospace';

  function lbl(x, y, text, color) {
    ctx.fillStyle = color || 'rgba(251, 192, 45, 0.85)';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, px(x), py(y));
  }

  // Row 1 top V — ~9cm labels
  lbl(2.0, 2.8, '~9', 'rgba(251, 192, 45, 0.7)');
  lbl(7.5, 2.8, '~9', 'rgba(251, 192, 45, 0.7)');
  lbl(13.0, 2.8, '~9', 'rgba(251, 192, 45, 0.7)');
  lbl(18.5, 2.8, '~9', 'rgba(251, 192, 45, 0.7)');

  // Rows 2-5 diamond — ~7cm labels (sample key cells)
  lbl(1.5, 9.0, '~7', 'rgba(251, 192, 45, 0.55)');
  lbl(3.8, 9.0, '~7', 'rgba(251, 192, 45, 0.55)');
  lbl(6.5, 9.5, '~7', 'rgba(251, 192, 45, 0.55)');
  lbl(9.2, 9.5, '~7', 'rgba(251, 192, 45, 0.55)');
  lbl(12.0, 9.5, '~7', 'rgba(251, 192, 45, 0.55)');
  lbl(14.5, 9.0, '~7', 'rgba(251, 192, 45, 0.55)');
  lbl(17.0, 9.5, '~7', 'rgba(251, 192, 45, 0.55)');
  lbl(19.5, 9.0, '~7', 'rgba(251, 192, 45, 0.55)');

  // More ~7 labels in middle rows
  lbl(1.5, 14.5, '~7', 'rgba(251, 192, 45, 0.55)');
  lbl(3.8, 14.5, '~7', 'rgba(251, 192, 45, 0.55)');
  lbl(12.0, 14.5, '~7', 'rgba(251, 192, 45, 0.55)');
  lbl(19.5, 14.5, '~7', 'rgba(251, 192, 45, 0.55)');

  lbl(6.5, 19.5, '~7', 'rgba(251, 192, 45, 0.55)');
  lbl(9.2, 19.5, '~7', 'rgba(251, 192, 45, 0.55)');
  lbl(17.0, 19.5, '~7', 'rgba(251, 192, 45, 0.55)');
  lbl(14.5, 19.5, '~7', 'rgba(251, 192, 45, 0.55)');

  lbl(1.5, 24.5, '~7', 'rgba(251, 192, 45, 0.55)');
  lbl(3.8, 24.5, '~7', 'rgba(251, 192, 45, 0.55)');
  lbl(17.0, 24.5, '~7', 'rgba(251, 192, 45, 0.55)');
  lbl(19.5, 24.5, '~7', 'rgba(251, 192, 45, 0.55)');

  // Row 6 bottom Λ — ~9cm labels
  lbl(2.0, 31.5, '~9', 'rgba(251, 192, 45, 0.7)');
  lbl(7.5, 31.5, '~9', 'rgba(251, 192, 45, 0.7)');
  lbl(13.0, 31.5, '~9', 'rgba(251, 192, 45, 0.7)');
  lbl(18.5, 31.5, '~9', 'rgba(251, 192, 45, 0.7)');

  // ── Dimension labels ──
  ctx.font = 'bold 13px "JetBrains Mono", monospace';
  ctx.fillStyle = '#00ffd5';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  ctx.fillText('21 cm', W / 2, H - 16);

  ctx.save();
  ctx.translate(12, H / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.textBaseline = 'middle';
  ctx.fillText('34 cm', 0, 0);
  ctx.restore();

  // ── Vertex dots ──
  const dotColor = 'rgba(0, 255, 213, 0.75)';
  function dot(x, y, r) {
    ctx.beginPath();
    ctx.arc(px(x), py(y), r || 2.5, 0, Math.PI * 2);
    ctx.fillStyle = dotColor;
    ctx.fill();
  }

  // Top V apexes
  dot(5.25, 7, 3);
  dot(15.75, 7, 3);

  // Bottom Λ apexes
  dot(5.25, 27, 3);
  dot(15.75, 27, 3);

  // X-crossing centers in rows 2-5
  yCells.forEach(([y0, y1]) => {
    const my = (y0 + y1) / 2;
    xCells.forEach(([x0, x1]) => {
      dot((x0 + x1) / 2, my);
    });
  });

  // Sub-center vertical intersections with horizontal lines
  [7, 12, 17, 22, 27].forEach(y => {
    dot(5.25, y);
    dot(15.75, y);
  });

  // Center vertical intersections
  [0, 7, 12, 17, 22, 27, 34].forEach(y => {
    dot(10.5, y, 3);
  });
}

// ── Init ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  initParticles();
  updateSim();
});
