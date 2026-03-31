/* ============================================================
   Granas Module — Platform JavaScript
   Navigation, Simulator, Blueprint Canvas, Particles
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

  for (let i = 0; i < 40; i++) {
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
  document.getElementById('result-power').innerHTML  = power.toFixed(4) + '<span class="result-metric-unit"> W</span>';
  document.getElementById('result-voc').innerHTML    = voc.toFixed(3) + '<span class="result-metric-unit"> V</span>';
  document.getElementById('result-isc').innerHTML    = isc.toFixed(4) + '<span class="result-metric-unit"> A</span>';
  document.getElementById('result-ff').innerHTML     = ff.toFixed(3);
  document.getElementById('result-annual').innerHTML = annual.toFixed(4) + '<span class="result-metric-unit"> kWh</span>';
  document.getElementById('result-cf').innerHTML     = cf.toFixed(2) + '<span class="result-metric-unit">' + (cf >= 0.20 ? ' MX' : '') + '</span>';
}

// ── Blueprint Canvas ─────────────────────────────────────
// Exact reproduction of the hand-drawn 17×10.5 cm Granas Blueprint
// Tracing from the hand drawing: top V, full-width X, split Xs, center split Xs, mirror
function drawBlueprint() {
  const canvas = document.getElementById('blueprintCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const W = canvas.width;
  const H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const pad = 20;
  const drawW = W - 2 * pad;
  const drawH = H - 2 * pad;
  const sx = drawW / 10.5;
  const sy = drawH / 17.0;

  function px(x) { return pad + x * sx; }
  function py(y) { return pad + y * sy; }

  const g1 = 'rgba(0, 255, 213, 0.07)';
  const g2 = 'rgba(0, 255, 136, 0.055)';
  const g3 = 'rgba(0, 200, 150, 0.065)';
  const g4 = 'rgba(100, 255, 180, 0.06)';

  function fillPoly(points, color) {
    ctx.beginPath();
    ctx.moveTo(px(points[0][0]), py(points[0][1]));
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(px(points[i][0]), py(points[i][1]));
    }
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
  }

  // ── ROW 1: Top V — two 5.5 triangles (y:0→2.5) ──
  fillPoly([[0,0], [5.25,0], [5.25,2.5]], g1);
  fillPoly([[5.25,0], [10.5,0], [5.25,2.5]], g2);

  // ── ROW 2: Full-width X (y:2.5→5) — labeled 3.5,3.5 ──
  // Diags: (0,2.5)→(10.5,5) and (10.5,2.5)→(0,5), crossing at (5.25,3.75)
  fillPoly([[0,2.5], [5.25,2.5], [5.25,3.75]], g3);
  fillPoly([[5.25,2.5], [10.5,2.5], [5.25,3.75]], g1);
  fillPoly([[0,2.5], [5.25,3.75], [0,5]], g4);
  fillPoly([[10.5,2.5], [5.25,3.75], [10.5,5]], g2);
  fillPoly([[0,5], [5.25,3.75], [5.25,5]], g1);
  fillPoly([[5.25,5], [5.25,3.75], [10.5,5]], g3);

  // ── ROW 3: Split X with center vertical (y:5→7) — labeled 3.5,3.5 ──
  // Left X: (0,5)-(5.25,5)-(5.25,7)-(0,7), crossing at (2.625,6)
  // Right X: (5.25,5)-(10.5,5)-(10.5,7)-(5.25,7), crossing at (7.875,6)
  fillPoly([[0,5], [5.25,5], [2.625,6]], g2);
  fillPoly([[0,5], [2.625,6], [0,7]], g3);
  fillPoly([[5.25,5], [5.25,7], [2.625,6]], g4);
  fillPoly([[0,7], [2.625,6], [5.25,7]], g1);
  fillPoly([[5.25,5], [10.5,5], [7.875,6]], g1);
  fillPoly([[5.25,5], [7.875,6], [5.25,7]], g2);
  fillPoly([[10.5,5], [10.5,7], [7.875,6]], g3);
  fillPoly([[5.25,7], [7.875,6], [10.5,7]], g4);

  // ── ROW 4: Center split X (y:7→10) — labeled 3,3 ──
  // Left X: (0,7)-(5.25,7)-(5.25,10)-(0,10), crossing at (2.625,8.5)
  // Right X: (5.25,7)-(10.5,7)-(10.5,10)-(5.25,10), crossing at (7.875,8.5)
  fillPoly([[0,7], [5.25,7], [2.625,8.5]], g3);
  fillPoly([[0,7], [2.625,8.5], [0,10]], g1);
  fillPoly([[5.25,7], [5.25,10], [2.625,8.5]], g2);
  fillPoly([[0,10], [2.625,8.5], [5.25,10]], g4);
  fillPoly([[5.25,7], [10.5,7], [7.875,8.5]], g4);
  fillPoly([[5.25,7], [7.875,8.5], [5.25,10]], g1);
  fillPoly([[10.5,7], [10.5,10], [7.875,8.5]], g2);
  fillPoly([[5.25,10], [7.875,8.5], [10.5,10]], g3);

  // ── ROW 5: Split X with center vertical (y:10→12) — labeled 3.5,3.5 ──
  // Mirror of Row 3
  fillPoly([[0,10], [5.25,10], [2.625,11]], g1);
  fillPoly([[0,10], [2.625,11], [0,12]], g4);
  fillPoly([[5.25,10], [5.25,12], [2.625,11]], g3);
  fillPoly([[0,12], [2.625,11], [5.25,12]], g2);
  fillPoly([[5.25,10], [10.5,10], [7.875,11]], g2);
  fillPoly([[5.25,10], [7.875,11], [5.25,12]], g3);
  fillPoly([[10.5,10], [10.5,12], [7.875,11]], g1);
  fillPoly([[5.25,12], [7.875,11], [10.5,12]], g4);

  // ── ROW 6: Full-width X (y:12→14.5) — labeled 3.5,3.5 ──
  // Mirror of Row 2. Crossing at (5.25, 13.25)
  fillPoly([[0,12], [5.25,12], [5.25,13.25]], g4);
  fillPoly([[5.25,12], [10.5,12], [5.25,13.25]], g2);
  fillPoly([[0,12], [5.25,13.25], [0,14.5]], g1);
  fillPoly([[10.5,12], [5.25,13.25], [10.5,14.5]], g3);
  fillPoly([[0,14.5], [5.25,13.25], [5.25,14.5]], g3);
  fillPoly([[5.25,14.5], [5.25,13.25], [10.5,14.5]], g1);

  // ── ROW 7: Bottom Λ — two 5.5 triangles (y:14.5→17) ──
  fillPoly([[0,14.5], [5.25,17], [0,17]], g2);
  fillPoly([[10.5,14.5], [5.25,17], [10.5,17]], g1);

  // ═══════════════════════════════════════════════════════
  //  CFRP SKELETON LINES
  // ═══════════════════════════════════════════════════════
  const cfrpColor = 'rgba(0, 255, 213, 0.55)';
  const cfrpWidth = 2.0;

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

  // Horizontal lines
  edge(0, 2.5,  10.5, 2.5);
  edge(0, 5,    10.5, 5);
  edge(0, 7,    10.5, 7);
  edge(0, 10,   10.5, 10);
  edge(0, 12,   10.5, 12);
  edge(0, 14.5, 10.5, 14.5);

  // Vertical center — only in split-X rows (3, 4, 5)
  edge(5.25, 5,  5.25, 7);    // Row 3
  edge(5.25, 7,  5.25, 10);   // Row 4
  edge(5.25, 10, 5.25, 12);   // Row 5

  // Row 1: Top V
  edge(0, 0,    5.25, 2.5);
  edge(10.5, 0, 5.25, 2.5);

  // Row 2: Full-width X (no center vert)
  edge(0, 2.5,    10.5, 5);
  edge(10.5, 2.5, 0, 5);

  // Row 3: Split X — left
  edge(0, 5,      5.25, 7);
  edge(5.25, 5,   0, 7);
  // Row 3: Split X — right
  edge(5.25, 5,   10.5, 7);
  edge(10.5, 5,   5.25, 7);

  // Row 4: Split X — left
  edge(0, 7,      5.25, 10);
  edge(5.25, 7,   0, 10);
  // Row 4: Split X — right
  edge(5.25, 7,   10.5, 10);
  edge(10.5, 7,   5.25, 10);

  // Row 5: Split X — left
  edge(0, 10,     5.25, 12);
  edge(5.25, 10,  0, 12);
  // Row 5: Split X — right
  edge(5.25, 10,  10.5, 12);
  edge(10.5, 10,  5.25, 12);

  // Row 6: Full-width X (no center vert)
  edge(0, 12,     10.5, 14.5);
  edge(10.5, 12,  0, 14.5);

  // Row 7: Bottom Λ
  edge(0, 17,     5.25, 14.5);
  edge(10.5, 17,  5.25, 14.5);

  // ═══════════════════════════════════════════════════════
  //  LABELS
  // ═══════════════════════════════════════════════════════
  ctx.font = 'bold 11px "JetBrains Mono", monospace';

  function lbl(x, y, text) {
    ctx.fillStyle = 'rgba(251, 192, 45, 0.85)';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, px(x), py(y));
  }

  lbl(2.3, 1.0, '5.5');   lbl(7.9, 1.0, '5.5');
  lbl(2.0, 3.5, '3.5');   lbl(7.8, 3.5, '3.5');
  lbl(2.0, 5.6, '3.5');   lbl(8.0, 5.6, '3.5');
  lbl(2.2, 8.1, '3');     lbl(7.8, 8.1, '3');
  lbl(2.0, 10.6, '3');    lbl(8.0, 10.6, '3');
  lbl(2.0, 13.0, '3.5');  lbl(7.8, 13.0, '3.5');
  lbl(2.3, 16.0, '5.5');  lbl(7.9, 16.0, '5.5');

  // Dimension labels
  ctx.font = 'bold 13px "JetBrains Mono", monospace';
  ctx.fillStyle = '#00ffd5';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  ctx.fillText('10.5', W / 2, H - 14);

  ctx.save();
  ctx.translate(10, H / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.textBaseline = 'middle';
  ctx.fillText('17', 0, 0);
  ctx.restore();

  // Vertex dots
  const vx = 'rgba(0, 255, 213, 0.8)';
  function dot(x, y) {
    ctx.beginPath();
    ctx.arc(px(x), py(y), 3, 0, Math.PI * 2);
    ctx.fillStyle = vx;
    ctx.fill();
  }

  dot(5.25, 2.5);                      // top apex
  dot(5.25, 3.75);                     // Row 2 crossing
  dot(2.625, 6);   dot(7.875, 6);     // Row 3 X crossings
  dot(2.625, 8.5); dot(7.875, 8.5);   // Row 4 X crossings
  dot(2.625, 11);  dot(7.875, 11);    // Row 5 X crossings
  dot(5.25, 13.25);                    // Row 6 crossing
  dot(5.25, 14.5);                     // bottom apex
  dot(5.25, 6);  dot(5.25, 8.5); dot(5.25, 11); // center vertical
}

// ── Init ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  initParticles();
  updateSim();
});
