/*
============================================================
PROJECT : JARVIS MARK 5

FILE    : memory_hud.js

PATH    : hud\ui\memory_hud.js

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
*/

/**
 * J.A.R.V.I.S. MARK V — MEMORY HUD MODULE
 * ─────────────────────────────────────────
 * Displays memory state in the left panel and via widgets.
 * Architecture is designed to be a thin UI layer over any
 * memory backend — including Mem0 (MemZero) when you integrate it.
 *
 * Backend contract (what Python should send via WS):
 *
 *   { "type": "memory", "data": {
 *       "short": 0-100,          // short-term buffer fill %
 *       "long":  0-100,          // long-term store fill %
 *       "context": 0-100,        // active context window fill %
 *       "event": {               // optional: a single memory event to log
 *         "type": "SAVE"|"READ"|"RECALL"|"FORGET"|"SCORE",
 *         "content": "...",
 *         "importance": 0-1      // optional importance score
 *       }
 *   }}
 *
 *   { "type": "memory_recall", "data": {
 *       "query": "...",
 *       "results": [ { "content": "...", "score": 0.92, "source": "long" }, ... ]
 *   }}
 *
 *   { "type": "user_profile", "data": {
 *       "name": "...", "mode": "friendly|professional|admin",
 *       "projects": [...], "preferences": {...}
 *   }}
 *
 * Mem0 integration points (when you add it):
 *   - memory.py calls mem0.add(text, user_id=...) on every important fact
 *   - memory.py calls mem0.search(query, user_id=...) for semantic recall
 *   - Results arrive via WS as "memory_recall" events
 *   - This file displays them — no changes needed here when you integrate
 */

'use strict';

window.MemoryHUD = (function () {

  /* ── Event log (last 100 memory events, newest first) ── */
  const _log = [];
  const MAX_LOG = 100;

  /* ── Current memory state ── */
  const _state = { short: 0, long: 0, context: 0 };

  /* ── User profile ── */
  let _profile = {};

  /* ══════════════════════════════════════════════════════
     PUBLIC: applyMemoryUpdate
     Called from script.js handleWSMessage for type:"memory"
     ══════════════════════════════════════════════════════ */
  function applyMemoryUpdate(data) {
    // Update fill bars
    if (data.short   != null) _setBar(0, data.short);
    if (data.long    != null) _setBar(1, data.long);
    if (data.context != null) _setBar(2, data.context);

    Object.assign(_state, {
      short:   data.short   ?? _state.short,
      long:    data.long    ?? _state.long,
      context: data.context ?? _state.context,
    });

    // Log a memory event if supplied
    if (data.event) {
      _logEvent(data.event);
    }

    // Show widget if a significant event
    if (data.event && data.event.importance >= 0.7 && window.WidgetEngine) {
      window.WidgetEngine.show('memory', {
        type:    data.event.type,
        content: data.event.content,
        ttl:     8000,
      });
    }
  }

  /* ══════════════════════════════════════════════════════
     PUBLIC: applyRecall
     Called from handleWSMessage for type:"memory_recall"
     Shows recall results as a widget
     ══════════════════════════════════════════════════════ */
  function applyRecall(data) {
    if (!data.results || !data.results.length) return;

    // Log each result
    data.results.forEach(r => {
      _logEvent({
        type:    'RECALL',
        content: `[${(r.score*100).toFixed(0)}%] ${r.content}`,
      });
    });

    // Widget: top 3 results
    if (window.WidgetEngine) {
      const lines = data.results.slice(0,3).map(r =>
        `<div class="widget-row">
           <span class="wl">${(r.score*100).toFixed(0)}%</span>
           <span class="wv" style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(r.content)}</span>
         </div>`
      ).join('');
      window.WidgetEngine.show('notification', {
        message: `RECALL: ${data.query}`,
        source:  'MEMORY SYSTEM',
        _html:   `<div style="margin-top:8px">${lines}</div>`,
        ttl: 10000,
      });
    }
  }

  /* ══════════════════════════════════════════════════════
     PUBLIC: applyUserProfile
     Updates personality mode indicator + stored profile
     ══════════════════════════════════════════════════════ */
  function applyUserProfile(data) {
    _profile = { ..._profile, ...data };

    // Update mode badge on top bar
    const badge = document.getElementById('connection-status');
    const modeMap = {
      professional: { label: '● PROFESSIONAL', color: '#00e5ff' },
      friendly:     { label: '● FRIENDLY',     color: '#00e676' },
      admin:        { label: '● ADMIN',         color: '#aa00ff' },
    };
    const m = modeMap[data.mode];
    if (m && badge) {
      badge.textContent    = m.label;
      badge.style.color    = m.color;
      badge.style.borderColor = m.color;
    }
  }

  /* ══════════════════════════════════════════════════════
     INTERNAL: set a fill bar in the left panel
     ══════════════════════════════════════════════════════ */
  function _setBar(index, pct) {
    const fills = document.querySelectorAll('.mem-fill');
    const vals  = document.querySelectorAll('.mem-val');
    if (fills[index]) {
      fills[index].style.width = pct + '%';
      // Color shift: cyan → yellow → red at high fill
      const hue = Math.max(0, 180 - pct * 1.8);
      fills[index].style.background = `hsl(${hue}, 100%, 55%)`;
      fills[index].style.boxShadow  = `0 0 6px hsl(${hue}, 100%, 55%)`;
    }
    if (vals[index]) vals[index].textContent = Math.round(pct) + '%';
  }

  /* ══════════════════════════════════════════════════════
     INTERNAL: add an event to the memory log panel
     (The left panel "MEMORY STATUS" section could optionally
      show an event log below the bars — we add it dynamically)
     ══════════════════════════════════════════════════════ */
  function _logEvent(event) {
    _log.unshift(event);
    if (_log.length > MAX_LOG) _log.length = MAX_LOG;

    // Inject a memory event log section if not present
    let logEl = document.getElementById('memory-event-log');
    if (!logEl) {
      const section = document.querySelector('.memory-grid');
      if (!section) return;
      logEl           = document.createElement('div');
      logEl.id        = 'memory-event-log';
      logEl.style.cssText = `margin-top:10px;max-height:80px;overflow-y:auto;display:flex;flex-direction:column;gap:3px`;
      section.parentNode.appendChild(logEl);
    }

    const row          = document.createElement('div');
    row.className      = 'mem-log-row';
    row.style.cssText  = `display:flex;gap:6px;font-size:9px;line-height:1.4;animation:logFadeIn .3s ease-out`;
    row.innerHTML      = `
      <span style="flex-shrink:0;font-size:7px;padding:1px 4px;background:rgba(0,229,255,.12);color:#00e5ff;border-radius:2px;height:fit-content;margin-top:1px">${_esc(event.type||'MEM')}</span>
      <span style="color:rgba(232,244,248,.6);font-size:9px">${_esc(event.content||'')}</span>`;

    logEl.insertBefore(row, logEl.firstChild);
    while (logEl.children.length > 8) logEl.removeChild(logEl.lastChild);
  }

  function _esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  /* ══════════════════════════════════════════════════════
     PUBLIC
     ══════════════════════════════════════════════════════ */
  return {
    applyMemoryUpdate,
    applyRecall,
    applyUserProfile,
    getState: () => ({ ..._state }),
    getProfile: () => ({ ..._profile }),
  };

})();
