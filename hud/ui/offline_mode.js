/*
============================================================
PROJECT : JARVIS MARK 5

FILE    : offline_mode.js

PATH    : hud\ui\offline_mode.js

PURPOSE :
Controls Offline Mode interface.

LAST UPDATED :
2026-06-28

============================================================
*/

/**
 * J.A.R.V.I.S. MARK V — OFFLINE / STANDBY MODE
 * Drives the standby overlay: clock, countdown, passive message rotation.
 */

'use strict';

window.OfflineMode = (function () {

  const $ = id => document.getElementById(id);

  let _clockInt   = null;
  let _cdInt      = null;
  let _msgInt     = null;
  let _msgIdx     = 0;

  const PASSIVE_MSGS = [
    'PASSIVE SENSORS ACTIVE',
    'MONITORING ENVIRONMENT',
    'AWAITING WAKE COMMAND',
    'PERIMETER SECURE',
    'THERMAL SCAN NOMINAL',
    'SECURITY SWEEP RUNNING',
    'NETWORK MONITORING ACTIVE',
    'BIOMETRIC SCAN IDLE',
  ];

  /* ──────────────────────────────────────────────
     ENTER standby
  ──────────────────────────────────────────────── */
  function enter(opts = {}) {
    // Show last command
    const lastCmdEl = document.getElementById('last-cmd');
    $('sb-last-cmd').textContent = lastCmdEl ? (lastCmdEl.textContent || '—') : '—';

    // Countdown
    const secs = opts.countdownSecs || 0;
    if (secs > 0) {
      const returnAt = new Date(Date.now() + secs * 1000);
      $('sb-return').textContent = _fmt12(returnAt);
      _startCountdown(secs);
    } else {
      $('sb-return').textContent   = 'UNSPECIFIED';
      $('sb-countdown').textContent = '—';
    }

    $('sb-status').textContent = 'DORMANT';

    // Clock
    _tickClock();
    _clockInt = setInterval(_tickClock, 1000);

    // Passive message rotation
    $('sb-monitoring').textContent = PASSIVE_MSGS[0];
    _msgInt = setInterval(() => {
      _msgIdx = (_msgIdx + 1) % PASSIVE_MSGS.length;
      const el = $('sb-monitoring');
      if (!el) return;
      el.style.opacity = '0';
      setTimeout(() => { el.textContent = PASSIVE_MSGS[_msgIdx]; el.style.opacity = '1'; }, 280);
    }, 4500);
  }

  /* ──────────────────────────────────────────────
     EXIT standby
  ──────────────────────────────────────────────── */
  function exit() {
    clearInterval(_clockInt);
    clearInterval(_cdInt);
    clearInterval(_msgInt);
    _clockInt = _cdInt = _msgInt = null;

    // If this was a timed standby triggered by wakeup → play Spotify
    if (window.JARVIS && window.JARVIS.triggerWakeUp) {
      window.JARVIS.triggerWakeUp();
    }
  }

  /* ──────────────────────────────────────────────
     CLOCK
  ──────────────────────────────────────────────── */
  function _tickClock() {
    const el = $('sb-time');
    if (!el) return;
    const n  = new Date();
    el.textContent = `${_p(n.getHours())}:${_p(n.getMinutes())}:${_p(n.getSeconds())}`;
  }

  function _fmt12(d) {
    return `${_p(d.getHours())}:${_p(d.getMinutes())}`;
  }

  function _p(n) { return String(n).padStart(2,'0'); }

  /* ──────────────────────────────────────────────
     COUNTDOWN
  ──────────────────────────────────────────────── */
  function _startCountdown(total) {
    let rem = total;
    _renderCountdown(rem);
    _cdInt = setInterval(() => {
      rem--;
      if (rem <= 0) {
        clearInterval(_cdInt);
        _cdInt = null;
        $('sb-countdown').textContent = 'NOW';
        $('sb-status').textContent    = 'RETURN EXPECTED';
        // Auto-wake after 3s
        setTimeout(() => {
          if (window.TransitionManager && window.TransitionManager.currentMode === 'standby') {
            window.TransitionManager.switchTo('online');
          }
        }, 3000);
        return;
      }
      _renderCountdown(rem);
    }, 1000);
  }

  function _renderCountdown(secs) {
    const el = $('sb-countdown');
    if (!el) return;
    const h  = Math.floor(secs / 3600);
    const m  = Math.floor((secs % 3600) / 60);
    const s  = secs % 60;
    el.textContent = h > 0
      ? `${_p(h)}:${_p(m)}:${_p(s)}`
      : `${_p(m)}:${_p(s)}`;
  }

  return { enter, exit };

})();
