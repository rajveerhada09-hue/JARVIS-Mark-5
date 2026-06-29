/*
============================================================
PROJECT : JARVIS MARK 5

FILE    : transition_manager.js

PATH    : hud\ui\transition_manager.js

PURPOSE :
Handles HUD transitions and visual animations.

LAST UPDATED :
2026-06-28

============================================================
*/

/**
 * J.A.R.V.I.S. MARK V — TRANSITION MANAGER
 * Orchestrates cinematic mode switches: online ↔ standby ↔ processor
 * No page reload. No flash. Pure CSS transitions.
 */

'use strict';

window.TransitionManager = (function () {

  let _mode         = 'online';   // 'online' | 'standby' | 'processor'
  let _transitioning = false;

  /* ── DOM ── */
  const hudMain   = document.getElementById('hud-main');
  const topBar    = document.getElementById('top-bar');
  const bottomBar = document.getElementById('bottom-bar');
  const sbOvl     = document.getElementById('standby-overlay');
  const prOvl     = document.getElementById('processor-overlay');
  const bgLayer   = document.getElementById('bg-layer');
  const modeBtns  = document.querySelectorAll('.mode-btn');

  /* ──────────────────────────────────────────────
     PUBLIC: switchTo(mode, opts)
  ──────────────────────────────────────────────── */
  function switchTo(mode, opts = {}) {
    if (mode === _mode || _transitioning) return;
    _transitioning = true;
    const from = _mode;
    _mode = mode;

    // Update dock highlight
    modeBtns.forEach(b => b.classList.toggle('mode-btn--active', b.dataset.mode === mode));

    document.dispatchEvent(new CustomEvent('modeChange', { detail: { from, to: mode, opts } }));

    _runTransition(from, mode, opts).finally(() => { _transitioning = false; });
  }

  /* ──────────────────────────────────────────────
     CHOREOGRAPHY
  ──────────────────────────────────────────────── */
  async function _runTransition(from, to, opts) {
    if (from === 'online'    && to === 'standby')   { await _toStandby(opts); }
    else if (from === 'standby'   && to === 'online')    { await _fromStandby(); }
    else if (from === 'online'    && to === 'processor') { await _toProcessor(); }
    else if (from === 'processor' && to === 'online')    { await _fromProcessor(); }
    else if (from === 'standby'   && to === 'processor') { await _fromStandby(); await _sleep(180); await _toProcessor(); }
    else if (from === 'processor' && to === 'standby')   { await _fromProcessor(); await _sleep(180); await _toStandby(opts); }
  }

  /* ── online → standby ── */
  async function _toStandby(opts) {
    // Dim BG to near-black with warm tint
    bgLayer.style.transition  = 'filter 1.2s ease';
    bgLayer.style.filter      = 'brightness(0.2) saturate(0.2) sepia(0.3)';

    // Blur + fade HUD content
    _fade(hudMain,   'out', 600, 'blur(6px) scale(0.97)');
    await _sleep(450);
    _fade(topBar,    'out', 350);
    _fade(bottomBar, 'out', 350);
    await _sleep(450);

    // Reveal standby overlay
    sbOvl.style.cssText = 'display:flex;opacity:0;transform:scale(1.04)';
    sbOvl.setAttribute('aria-hidden', 'false');
    await _sleep(20);
    sbOvl.style.transition = 'opacity .9s ease,transform .9s cubic-bezier(.16,1,.3,1)';
    sbOvl.style.opacity    = '1';
    sbOvl.style.transform  = 'scale(1)';

    if (window.OfflineMode) window.OfflineMode.enter(opts);
    await _sleep(900);
  }

  /* ── standby → online ── */
  async function _fromStandby() {
    // Reactor surge flash
    sbOvl.style.boxShadow = 'inset 0 0 120px rgba(255,140,0,.4)';
    await _sleep(100);
    sbOvl.style.boxShadow = '';

    sbOvl.style.transition = 'opacity .65s ease,transform .65s ease';
    sbOvl.style.opacity    = '0';
    sbOvl.style.transform  = 'scale(0.96)';
    await _sleep(380);

    // Restore background
    bgLayer.style.filter = 'brightness(1) saturate(1) sepia(0)';

    // Restore HUD panels
    _fade(topBar,    'in', 480);
    _fade(bottomBar, 'in', 480);
    _fade(hudMain,   'in', 680, 'none');
    await _sleep(680);

    sbOvl.style.display = 'none';
    sbOvl.setAttribute('aria-hidden', 'true');
    if (window.OfflineMode) window.OfflineMode.exit();
    if (window.OnlineMode)  window.OnlineMode.resume();
    await _sleep(200);
  }

  /* ── online → processor ── */
  async function _toProcessor() {
    _fade(hudMain, 'out', 480, 'blur(4px) scale(0.98)');
    await _sleep(360);
    _fade(topBar, 'out', 280);
    await _sleep(280);

    prOvl.style.cssText = 'display:flex;opacity:0;transform:translateY(14px)';
    prOvl.setAttribute('aria-hidden', 'false');
    await _sleep(20);
    prOvl.style.transition = 'opacity .55s ease,transform .55s cubic-bezier(.16,1,.3,1)';
    prOvl.style.opacity    = '1';
    prOvl.style.transform  = 'translateY(0)';

    if (window.ProcessorMode) window.ProcessorMode.enter();
    await _sleep(560);
  }

  /* ── processor → online ── */
  async function _fromProcessor() {
    prOvl.style.transition = 'opacity .45s ease,transform .45s ease';
    prOvl.style.opacity    = '0';
    prOvl.style.transform  = 'translateY(10px)';
    await _sleep(360);

    prOvl.style.display = 'none';
    prOvl.setAttribute('aria-hidden', 'true');

    _fade(topBar,  'in', 380);
    _fade(hudMain, 'in', 560, 'none');

    if (window.ProcessorMode) window.ProcessorMode.exit();
    if (window.OnlineMode)    window.OnlineMode.resume();
    await _sleep(560);
  }

  /* ──────────────────────────────────────────────
     HELPERS
  ──────────────────────────────────────────────── */
  function _fade(el, dir, dur, transform) {
    if (!el) return;
    el.style.transition = `opacity ${dur}ms ease`
      + (transform ? `,filter ${dur}ms ease,transform ${dur}ms ease` : '');
    if (dir === 'out') {
      el.style.opacity = '0';
      if (transform) el.style.transform = transform;
    } else {
      el.style.opacity = '1';
      if (transform === 'none') { el.style.transform = 'none'; el.style.filter = 'none'; }
    }
  }

  function _sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  /* ──────────────────────────────────────────────
     DOCK BUTTONS
  ──────────────────────────────────────────────── */
  modeBtns.forEach(btn => {
    btn.addEventListener('click', () => switchTo(btn.dataset.mode));
  });

  /* ──────────────────────────────────────────────
     PUBLIC
  ──────────────────────────────────────────────── */
  return {
    switchTo,
    get currentMode() { return _mode; },
  };

})();
