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
function drawBlueprint() {
  const canvas = document.getElementById('blueprintCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const W = canvas.width;
  const H = canvas.height;

  // Clear
  ctx.clearRect(0, 0, W, H);

  // Scale: 10.5 cm → W px, 17 cm → H px
  const sx = W / 10.5;
  const sy = H / 17.0;
  const pad = 10;

  // Helper: draw a filled triangle with green tint
  function fillTri(x1, y1, x2, y2, x3, y3, color) {
    ctx.beginPath();
    ctx.moveTo(pad + x1 * sx, pad + y1 * sy);
    ctx.lineTo(pad + x2 * sx, pad + y2 * sy);
    ctx.lineTo(pad + x3 * sx, pad + y3 * sy);
    ctx.closePath();
    ctx.fillStyle = color || 'rgba(0, 255, 213, 0.06)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(0, 255, 213, 0.4)';
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }

  // Helper: draw line
  function drawLine(x1, y1, x2, y2, color, width) {
    ctx.beginPath();
    ctx.moveTo(pad + x1 * sx, pad + y1 * sy);
    ctx.lineTo(pad + x2 * sx, pad + y2 * sy);
    ctx.strokeStyle = color || 'rgba(0, 255, 213, 0.35)';
    ctx.lineWidth = width || 1.5;
    ctx.stroke();
  }

  // Helper: label
  function label(x, y, text, color) {
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.fillStyle = color || 'rgba(0, 255, 213, 0.6)';
    ctx.textAlign = 'center';
    ctx.fillText(text, pad + x * sx, pad + y * sy);
  }

  // Panel border
  ctx.strokeStyle = 'rgba(0, 255, 213, 0.6)';
  ctx.lineWidth = 2;
  ctx.strokeRect(pad, pad, 10.5 * sx, 17 * sy);

  // Row definitions from the hand-drawn blueprint (top to bottom)
  // Row 1: Top triangles (5.5 + 5.5)
  const green1 = 'rgba(0, 255, 213, 0.08)';
  const green2 = 'rgba(0, 255, 136, 0.06)';
  const green3 = 'rgba(0, 200, 150, 0.07)';

  // Top row: two triangles pointing down
  fillTri(0, 0, 5.25, 2.5, 10.5, 0, green1);
  drawLine(0, 0, 5.25, 2.5);
  drawLine(10.5, 0, 5.25, 2.5);
  label(2.5, 1.2, '5.5', '#fbc02d');
  label(8.0, 1.2, '5.5', '#fbc02d');

  // Row 2: Diamonds at 3.5 cm (y: 2.5 → 5.5)
  fillTri(0, 2.5, 3.5, 5.0, 0, 5.0, green2);
  fillTri(0, 2.5, 3.5, 2.5, 3.5, 5.0, green3);
  fillTri(3.5, 2.5, 7.0, 2.5, 5.25, 5.0, green1);
  fillTri(3.5, 5.0, 7.0, 5.0, 5.25, 2.5, green2);
  fillTri(7.0, 2.5, 10.5, 2.5, 10.5, 5.0, green3);
  fillTri(7.0, 2.5, 7.0, 5.0, 10.5, 5.0, green1);
  drawLine(0, 2.5, 10.5, 2.5);
  drawLine(0, 5.0, 10.5, 5.0);
  drawLine(3.5, 2.5, 3.5, 5.0);
  drawLine(7.0, 2.5, 7.0, 5.0);
  drawLine(0, 2.5, 3.5, 5.0);
  drawLine(3.5, 2.5, 0, 5.0);
  drawLine(3.5, 2.5, 7.0, 5.0);
  drawLine(7.0, 2.5, 3.5, 5.0);
  drawLine(7.0, 2.5, 10.5, 5.0);
  drawLine(10.5, 2.5, 7.0, 5.0);
  label(1.5, 3.8, '3.5', '#fbc02d');
  label(5.25, 3.8, '3.5', '#fbc02d');
  label(9.0, 3.8, '3.5', '#fbc02d');

  // Row 3: Center diamonds at 3 cm (y: 5.0 → 7.5)
  fillTri(0, 5.0, 3.5, 5.0, 1.75, 7.0, green1);
  fillTri(0, 7.0, 3.5, 7.0, 1.75, 5.0, green2);
  fillTri(3.5, 5.0, 7.0, 5.0, 5.25, 7.0, green3);
  fillTri(3.5, 7.0, 7.0, 7.0, 5.25, 5.0, green1);
  fillTri(7.0, 5.0, 10.5, 5.0, 8.75, 7.0, green2);
  fillTri(7.0, 7.0, 10.5, 7.0, 8.75, 5.0, green3);
  drawLine(0, 7.0, 10.5, 7.0);
  drawLine(0, 5.0, 1.75, 7.0);
  drawLine(3.5, 5.0, 1.75, 7.0);
  drawLine(0, 7.0, 1.75, 5.0);
  drawLine(3.5, 7.0, 1.75, 5.0);
  drawLine(3.5, 5.0, 5.25, 7.0);
  drawLine(7.0, 5.0, 5.25, 7.0);
  drawLine(3.5, 7.0, 5.25, 5.0);
  drawLine(7.0, 7.0, 5.25, 5.0);
  drawLine(7.0, 5.0, 8.75, 7.0);
  drawLine(10.5, 5.0, 8.75, 7.0);
  drawLine(7.0, 7.0, 8.75, 5.0);
  drawLine(10.5, 7.0, 8.75, 5.0);
  label(1.75, 6.2, '3', '#fbc02d');
  label(5.25, 6.2, '3', '#fbc02d');
  label(8.75, 6.2, '3', '#fbc02d');

  // Row 4: 3.0 repeat (y: 7.0 → 9.5)
  fillTri(0, 7.0, 5.25, 9.5, 0, 9.5, green3);
  fillTri(5.25, 9.5, 10.5, 7.0, 10.5, 9.5, green1);
  drawLine(0, 9.5, 10.5, 9.5);
  drawLine(0, 7.0, 5.25, 9.5);
  drawLine(10.5, 7.0, 5.25, 9.5);
  label(2.5, 8.5, '3', '#fbc02d');
  label(8.0, 8.5, '3', '#fbc02d');

  // Row 5: 3.5 diamonds (y: 9.5 → 12.0)
  fillTri(0, 9.5, 3.5, 9.5, 1.75, 12.0, green2);
  fillTri(3.5, 9.5, 7.0, 9.5, 5.25, 12.0, green1);
  fillTri(7.0, 9.5, 10.5, 9.5, 8.75, 12.0, green3);
  fillTri(0, 12.0, 3.5, 12.0, 1.75, 9.5, green1);
  fillTri(3.5, 12.0, 7.0, 12.0, 5.25, 9.5, green3);
  fillTri(7.0, 12.0, 10.5, 12.0, 8.75, 9.5, green2);
  drawLine(0, 12.0, 10.5, 12.0);
  drawLine(0, 9.5, 1.75, 12.0);
  drawLine(3.5, 9.5, 1.75, 12.0);
  drawLine(3.5, 9.5, 5.25, 12.0);
  drawLine(7.0, 9.5, 5.25, 12.0);
  drawLine(7.0, 9.5, 8.75, 12.0);
  drawLine(10.5, 9.5, 8.75, 12.0);
  drawLine(0, 12.0, 1.75, 9.5);
  drawLine(3.5, 12.0, 1.75, 9.5);
  drawLine(3.5, 12.0, 5.25, 9.5);
  drawLine(7.0, 12.0, 5.25, 9.5);
  drawLine(7.0, 12.0, 8.75, 9.5);
  drawLine(10.5, 12.0, 8.75, 9.5);
  label(1.75, 11.0, '3.5', '#fbc02d');
  label(5.25, 11.0, '3.5', '#fbc02d');
  label(8.75, 11.0, '3.5', '#fbc02d');

  // Row 6: Bottom double triangles (y: 12.0 → 14.5)
  fillTri(0, 12.0, 5.25, 14.5, 10.5, 12.0, green2);
  drawLine(0, 12.0, 5.25, 14.5);
  drawLine(10.5, 12.0, 5.25, 14.5);
  drawLine(0, 14.5, 10.5, 14.5);
  label(2.5, 13.5, '5.5', '#fbc02d');
  label(8.0, 13.5, '5.5', '#fbc02d');

  // Row 7: Bottom triangles pointing up (y: 14.5 → 17)
  fillTri(0, 14.5, 5.25, 17.0, 0, 17.0, green1);
  fillTri(10.5, 14.5, 5.25, 17.0, 10.5, 17.0, green3);
  drawLine(0, 14.5, 5.25, 17.0);
  drawLine(10.5, 14.5, 5.25, 17.0);

  // Dimension labels
  ctx.font = 'bold 12px "JetBrains Mono", monospace';
  ctx.fillStyle = '#00ffd5';
  ctx.textAlign = 'center';
  ctx.fillText('10.5', W / 2, H - 2);

  ctx.save();
  ctx.translate(8, H / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText('17', 0, 0);
  ctx.restore();
}

// ── Init ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  initParticles();
  updateSim();
});
