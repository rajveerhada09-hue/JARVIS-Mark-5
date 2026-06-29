/*
============================================================
PROJECT : JARVIS MARK 5

FILE    : online_mode.js

PATH    : hud\ui\online_mode.js

PURPOSE :
Controls Online Mode interface and widgets.

LAST UPDATED :
2026-06-28

============================================================
*/

/**
 * J.A.R.V.I.S. MARK V — ONLINE MODE
 * Handles state-specific reactor effects, module label updates,
 * and the wake-up flow when returning from standby.
 */

'use strict';

window.OnlineMode = (function () {

  /* ── Listen to AI state changes dispatched by script.js ── */
  document.addEventListener('jarvis:stateChange', e => {
    if (window.TransitionManager && window.TransitionManager.currentMode !== 'online') return;
    _applyStateEffects(e.detail);
  });

  /* ── State→effect map ── */
  const STATE_EFFECTS = {
    listening:  { notif: 'Voice recognition active — awaiting directive.' },
    thinking:   { notif: 'Neural inference in progress...' },
    speaking:   { notif: 'Voice output channel engaged.' },
    executing:  { notif: 'Executing command sequence.' },
    idle:       { notif: 'All systems nominal.' },
    error:      { notif: '⚠ System error — diagnostics recommended.' },
    offline:    { notif: 'Connection lost. Attempting reconnect...' },
  };

  function _applyStateEffects(s) {
    const eff = STATE_EFFECTS[s];
    if (eff && eff.notif && window.JARVIS) window.JARVIS.notify(eff.notif);
  }

  /* ── Called by TransitionManager after returning from any other mode ── */
  function resume() {
    // Nothing extra needed — CSS data-state on body handles visuals
    if (window.JARVIS) window.JARVIS.setState(window.JARVIS._lastState || 'idle');
  }

  return { resume };

})();
