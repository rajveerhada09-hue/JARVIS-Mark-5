/*
============================================================
PROJECT : JARVIS MARK 5

FILE    : processor_mode.js

PATH    : hud\ui\processor_mode.js

PURPOSE :
Controls Mission Control / Processor diagnostics interface.

LAST UPDATED :
2026-06-28

============================================================
*/

/**
 * J.A.R.V.I.S. MARK V — PROCESSOR MODE
 * Live hardware dashboard with holographic chip animation + webcam.
 */

'use strict';

window.ProcessorMode = (function () {

  const $ = id => document.getElementById(id);

  /* ── Internal handles ── */
  let _chipAnimId  = null;
  let _clockInt    = null;
  let _statsInt    = null;
  let _chipLoad    = 0;
  let _chipTarget  = 0;
  let _fpsSamples  = [];
  let _webcamStream = null;
  let _webcamMirror = false;

  /* ──────────────────────────────────────────────
     ENTER
  ──────────────────────────────────────────────── */
  function enter() {
    _startClock();
    _startChipAnim();
    _startStatsRefresh();
    _wireButtons();
  }

  /* ──────────────────────────────────────────────
     EXIT
  ──────────────────────────────────────────────── */
  function exit() {
    clearInterval(_clockInt);
    clearInterval(_statsInt);
    cancelAnimationFrame(_chipAnimId);
    _clockInt = _statsInt = _chipAnimId = null;
    _stopWebcam();
  }

  /* ──────────────────────────────────────────────
     HEADER CLOCK
  ──────────────────────────────────────────────── */
  function _startClock() {
    const tick = () => {
      const el = $('proc-header-time');
      if (!el) return;
      const n = new Date();
      el.textContent = `${_p(n.getHours())}:${_p(n.getMinutes())}:${_p(n.getSeconds())}`;
    };
    tick();
    _clockInt = setInterval(tick, 1000);
  }

  /* ──────────────────────────────────────────────
     LIVE STATS
     Mirrors values already rendered in the main HUD
     + adds processor-specific details.
  ──────────────────────────────────────────────── */
  function _startStatsRefresh() {
    _refreshStats();
    _statsInt = setInterval(_refreshStats, 2000);
  }

  function _refreshStats() {
    const cpuPct = _readGauge('cpu-val');
    const ramPct = _readGauge('ram-val');

    // CPU
    _chipTarget = cpuPct;
    _setBar('proc-cpu-fill', cpuPct);
    _setText('proc-cpu-pct', `${Math.round(cpuPct)}% LOAD`);

    // Cores / arch
    const cpuSubEl = $('cpu-sub');
    const cores = cpuSubEl ? cpuSubEl.textContent : '--';
    _setText('proc-cpu-arch', `x86_64 — ${cores}`);
    _setText('proc-threads',  String(_rnd(80, 320)));
    _setText('proc-clock',    (_rnd(20, 50) / 10).toFixed(1) + ' GHz');
    _setText('proc-power',    _rnd(35, 120) + ' W');

    // RAM
    _setBar('proc-ram-fill', ramPct);
    _setText('proc-ram-pct', `${Math.round(ramPct)}% USAGE`);
    const ramSubEl = $('ram-sub');
    if (ramSubEl) _setText('proc-ram-detail', ramSubEl.textContent);

    // Temperature
    const tempEl = $('stat-temp');
    if (tempEl) _setText('proc-temp', tempEl.textContent);

    // Battery
    const batEl = $('stat-battery');
    if (batEl) _setText('proc-battery', batEl.textContent);

    // Disk
    const diskPct = _readGauge('disk-c-val');
    _setBar('proc-storage-fill', diskPct);
    _setText('proc-storage', `${Math.round(diskPct)}% USED`);

    // Network
    const netUp = $('net-up');
    if (netUp) _setText('proc-net-speed', netUp.textContent);

    // Simulated extras
    _setText('proc-disk-read',  (_rnd(5, 300) / 10).toFixed(1) + ' MB/s');
    _setText('proc-disk-write', (_rnd(2, 120) / 10).toFixed(1) + ' MB/s');
    _setText('proc-latency',    _rnd(6, 55) + ' ms');
    _setText('proc-py-count',   String(_rnd(3, 16)));
    _setText('proc-bg-count',   String(_rnd(8, 28)) + ' running');
    _setText('proc-fps',        _currentFPS() + ' fps');

    // GPU (placeholder)
    const gpuPct = _readGauge('gpu-val');
    if (!isNaN(gpuPct)) {
      _setBar('proc-gpu-fill', gpuPct);
      _setText('proc-gpu-pct', `${Math.round(gpuPct)}% UTIL`);
      _setBar('proc-gpu-util-fill', gpuPct);
      _setText('proc-gpu-util-pct', `${Math.round(gpuPct)}%`);
    }

    // VRAM simulated
    const vramUsed  = _rnd(800, 3500);
    const vramTotal = 4096;
    _setText('proc-vram', `${vramUsed} MB / ${vramTotal} MB`);
    _setBar('proc-vram-fill', (vramUsed/vramTotal)*100);

    // Chip load bar color
    const lb = $('chip-load-bar');
    if (lb) {
      lb.style.width      = cpuPct + '%';
      lb.style.background = cpuPct > 80
        ? 'linear-gradient(90deg,#ff1744,#ffc400)'
        : cpuPct > 55
          ? 'linear-gradient(90deg,#00b8d4,#ffc400)'
          : 'linear-gradient(90deg,#1565c0,#00e5ff)';
    }
  }

  /* Called externally by script.js when real WS stats arrive */
  function applyStats(d) {
    if (window.TransitionManager && window.TransitionManager.currentMode !== 'processor') return;
    if (d.cpu         != null) { _setBar('proc-cpu-fill', d.cpu);  _setText('proc-cpu-pct', Math.round(d.cpu) + '% LOAD'); _chipTarget = d.cpu; }
    if (d.ram         != null) { _setBar('proc-ram-fill', d.ram);  _setText('proc-ram-pct', Math.round(d.ram) + '% USAGE'); }
    if (d.temperature != null) _setText('proc-temp',    d.temperature + ' °C');
    if (d.battery     != null) _setText('proc-battery', Math.round(d.battery) + '%');
    if (d.gpu         != null) { _setBar('proc-gpu-fill', d.gpu); _setBar('proc-gpu-util-fill', d.gpu); }
  }

  /* ──────────────────────────────────────────────
     MODULE STATUS
  ──────────────────────────────────────────────── */
  function setModuleStatus(name, status) {
    const el = document.querySelector(`.module-item[data-module="${name}"] .module-status`);
    if (!el) return;
    el.dataset.status  = status;
    el.textContent     = status.toUpperCase();
  }

  /* ──────────────────────────────────────────────
     CHIP ANIMATION
  ──────────────────────────────────────────────── */
  function _startChipAnim() {
    const chip  = $('proc-chip');
    const pulse = $('chip-core-pulse');
    const lanes = document.querySelectorAll('.chip-lane');

    (function frame() {
      _chipAnimId = requestAnimationFrame(frame);

      // Ease chip load
      _chipLoad += (_chipTarget - _chipLoad) * 0.04;

      // Micro wobble under high load
      if (chip) {
        const w = _chipLoad > 70 ? Math.sin(Date.now() / 80) * 0.35 : 0;
        chip.style.transform = `rotate(${w}deg)`;
      }

      // Pulse core brightness with load
      if (pulse) {
        const intensity = 0.3 + (_chipLoad / 100) * 0.7;
        pulse.style.opacity = String(0.4 + Math.sin(Date.now() / 480) * 0.3 * intensity);
      }

      // Lane data-packet animation (opacity ripple)
      const t = Date.now();
      lanes.forEach((lane, i) => {
        const phase = (t / 380 + i * 0.65) % (Math.PI * 2);
        lane.style.opacity = String(Math.sin(phase) * 0.5 + 0.5);
      });
    })();
  }

  /* ──────────────────────────────────────────────
     WEBCAM
  ──────────────────────────────────────────────── */
  function _wireButtons() {
    // Close button
    const closeBtn = $('proc-close-btn');
    if (closeBtn && !closeBtn._wired) {
      closeBtn._wired = true;
      closeBtn.addEventListener('click', () => {
        if (window.TransitionManager) window.TransitionManager.switchTo('online');
      });
    }

    // Webcam start
    const startBtn  = $('webcam-start-btn');
    const stopBtn   = $('webcam-stop-btn');
    const mirrorBtn = $('webcam-mirror-btn');

    if (startBtn && !startBtn._wired) {
      startBtn._wired = true;
      startBtn.addEventListener('click', _startWebcam);
    }
    if (stopBtn && !stopBtn._wired) {
      stopBtn._wired = true;
      stopBtn.addEventListener('click', _stopWebcam);
    }
    if (mirrorBtn && !mirrorBtn._wired) {
      mirrorBtn._wired = true;
      mirrorBtn.addEventListener('click', () => {
        _webcamMirror = !_webcamMirror;
        const vid = $('webcam-video');
        if (vid) vid.style.transform = _webcamMirror ? 'scaleX(-1)' : 'scaleX(1)';
      });
    }
  }

  async function _startWebcam() {
    const vid       = $('webcam-video');
    const statusTxt = $('webcam-status-text');
    const startBtn  = $('webcam-start-btn');
    const stopBtn   = $('webcam-stop-btn');
    if (!vid) return;

    try {
      _webcamStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      vid.srcObject = _webcamStream;
      vid.style.transform = _webcamMirror ? 'scaleX(-1)' : '';
      if (statusTxt) statusTxt.textContent = 'OPTICAL SENSOR — LIVE';
      if (startBtn)  startBtn.disabled = true;
      if (stopBtn)   stopBtn.disabled  = false;
      _startWebcamOverlay();
    } catch (e) {
      if (statusTxt) statusTxt.textContent = 'CAMERA ACCESS DENIED';
    }
  }

  function _stopWebcam() {
    if (_webcamStream) {
      _webcamStream.getTracks().forEach(t => t.stop());
      _webcamStream = null;
    }
    const vid    = $('webcam-video');
    if (vid) vid.srcObject = null;
    const txt = $('webcam-status-text');
    if (txt) txt.textContent = 'CAMERA OFFLINE';
    const startBtn = $('webcam-start-btn');
    const stopBtn  = $('webcam-stop-btn');
    if (startBtn) startBtn.disabled = false;
    if (stopBtn)  stopBtn.disabled  = true;
  }

  /* Draws HUD overlay lines on the webcam canvas */
  function _startWebcamOverlay() {
    const canvas = $('webcam-overlay-canvas');
    if (!canvas) return;
    const ctx    = canvas.getContext('2d');

    (function draw() {
      if (!_webcamStream) return;
      requestAnimationFrame(draw);
      const W = canvas.width  = canvas.offsetWidth;
      const H = canvas.height = canvas.offsetHeight;
      ctx.clearRect(0, 0, W, H);

      // Horizontal reticle lines
      ctx.strokeStyle = 'rgba(0,229,255,0.25)';
      ctx.lineWidth   = 0.5;
      [0.25, 0.5, 0.75].forEach(f => {
        ctx.beginPath(); ctx.moveTo(0, H*f); ctx.lineTo(W, H*f); ctx.stroke();
      });
      [0.33, 0.67].forEach(f => {
        ctx.beginPath(); ctx.moveTo(W*f, 0); ctx.lineTo(W*f, H); ctx.stroke();
      });

      // Center crosshair
      const cx = W/2, cy = H/2, cs = 20;
      ctx.strokeStyle = 'rgba(0,229,255,0.6)';
      ctx.lineWidth   = 1;
      ctx.beginPath();
      ctx.moveTo(cx - cs, cy); ctx.lineTo(cx + cs, cy);
      ctx.moveTo(cx, cy - cs); ctx.lineTo(cx, cy + cs);
      ctx.stroke();

      // Pulsing radius
      const r = 16 + Math.sin(Date.now()/600) * 4;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI*2);
      ctx.strokeStyle = 'rgba(0,229,255,0.35)';
      ctx.stroke();

      // Corner markers
      const m = 18;
      ctx.strokeStyle = 'rgba(0,229,255,0.8)';
      ctx.lineWidth   = 1.5;
      [[8,8],[W-8,8],[8,H-8],[W-8,H-8]].forEach(([x,y]) => {
        const sx = x < W/2 ? 1 : -1, sy = y < H/2 ? 1 : -1;
        ctx.beginPath();
        ctx.moveTo(x, y + sy*m); ctx.lineTo(x, y); ctx.lineTo(x + sx*m, y);
        ctx.stroke();
      });
    })();
  }

  /* ──────────────────────────────────────────────
     HELPERS
  ──────────────────────────────────────────────── */
  function _setText(id, txt) { const e = $(id); if (e) e.textContent = txt; }
  function _setBar(id, pct)  { const e = $(id); if (e) e.style.width = Math.max(0,Math.min(100,pct)) + '%'; }
  function _readGauge(id)    { const e = $(id); return e ? parseFloat(e.textContent) || 0 : 0; }
  function _rnd(a, b)        { return Math.floor(Math.random() * (b-a+1)) + a; }
  function _p(n)             { return String(n).padStart(2,'0'); }

  function _currentFPS() {
    const now = performance.now();
    _fpsSamples.push(now);
    _fpsSamples = _fpsSamples.filter(t => now - t < 1000);
    return _fpsSamples.length;
  }

  /* ──────────────────────────────────────────────
     PUBLIC
  ──────────────────────────────────────────────── */
  return { enter, exit, applyStats, setModuleStatus };

})();
