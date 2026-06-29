/*
============================================================
PROJECT : JARVIS MARK 5

FILE    : widget_engine.js

PATH    : hud\ui\widget_engine.js

PURPOSE :
Creates, updates and manages draggable HUD widgets.

LAST UPDATED :
2026-06-28

============================================================
*/

/**
 * J.A.R.V.I.S. MARK V — WIDGET ENGINE
 * ─────────────────────────────────────
 * Modular, event-driven widget system.
 * Widgets appear inside the HUD — never as browser popups.
 *
 * Architecture:
 *   WidgetEngine.register(id, definition)  → registers a widget blueprint
 *   WidgetEngine.show(id, data)            → mounts + animates the widget in
 *   WidgetEngine.hide(id)                  → animates out + unmounts
 *   WidgetEngine.update(id, data)          → live-patches a visible widget
 *   WidgetEngine.toggle(id, data)          → show if hidden, hide if visible
 *
 * Widgets live in #widget-layer (injected into #core-center).
 * Each widget is a self-contained <div class="widget"> with an
 * optional auto-hide timer and a refresh interval.
 *
 * Backend sends:  { "type": "widget", "data": { "id": "weather", "action": "show"|"hide"|"update", ...payload } }
 */

'use strict';

window.WidgetEngine = (function () {

  /* ── Container (injected into DOM on init) ── */
  let _layer = null;
  const _layoutStoreKey = 'jarvis-widget-layout';
  let _layouts = _loadLayouts();

  /* ── Registry: id → { def, el, hideTimer, refreshId } ── */
  const _registry  = {};
  const _active    = {};   // currently mounted widgets

  /* ═══════════════════════════════════════════════════════
     CORE API
     ═══════════════════════════════════════════════════════ */

  /** Register a widget blueprint. Must be called before show(). */
  function register(id, def) {
    _registry[id] = def;
  }

  /** Mount and animate a widget into the HUD. */
  function show(id, data = {}) {
    const def = _registry[id];
    if (!def) { console.warn(`[WidgetEngine] Unknown widget: ${id}`); return; }
    if (_active[id]) { update(id, data); return; }

    const el = _buildEl(id, def, data);
    _layer.appendChild(el);

    // Position the widget
    _positionWidget(el, def.position || 'center');
    _handleLifecycle(el, id, def, data);

    // Animate in
    requestAnimationFrame(() => {
      el.style.opacity   = '1';
      el.style.transform = 'scale(1) translateY(0)';
    });

    // Auto-hide after ttl ms (0 = persistent)
    let hideTimer = null;
    const ttl = data.ttl ?? def.ttl ?? 0;
    if (ttl > 0) {
      hideTimer = setTimeout(() => hide(id), ttl);
    }

    // Optional periodic refresh
    let refreshId = null;
    if (def.refresh && typeof def.refresh === 'function' && def.refreshInterval > 0) {
      refreshId = setInterval(() => {
        if (_active[id]) def.refresh(_active[id].el, _active[id].data);
      }, def.refreshInterval);
    }

    _active[id] = { el, data: { ...data }, hideTimer, refreshId };
    _saveLayout(id, { visible: true, data: { ...data } });
  }

  /** Remove widget with fade-out. */
  function hide(id) {
    const entry = _active[id];
    if (!entry) return;

    clearTimeout(entry.hideTimer);
    clearInterval(entry.refreshId);
    _cleanupWidget(entry.el);

    entry.el.style.opacity   = '0';
    entry.el.style.transform = 'scale(0.92) translateY(-8px)';
    _saveLayout(id, { visible: false });
    setTimeout(() => {
      if (entry.el.parentNode) entry.el.parentNode.removeChild(entry.el);
      delete _active[id];
    }, 400);
  }

  /** Live-patch data into an already-mounted widget. */
  function update(id, data = {}) {
    const entry = _active[id];
    if (!entry) { show(id, data); return; }
    const def = _registry[id];
    entry.data = { ...entry.data, ...data };
    _saveLayout(id, { data: entry.data, visible: true });
    if (def && typeof def.patch === 'function') {
      def.patch(entry.el, entry.data);
    }
  }

  function toggle(id, data = {}) {
    _active[id] ? hide(id) : show(id, data);
  }

  function destroy(id) {
    hide(id);
    _removeLayout(id);
  }

  function pinWidget(id) {
    const entry = _active[id];
    if (!entry) return;
    const el = entry.el;
    if (!el) return;
    _togglePin(el, id);
  }

  function saveLayout() {
    Object.keys(_active).forEach(id => {
      const entry = _active[id];
      if (entry && entry.el) _setWidgetLayoutFromElement(id, entry.el);
    });
  }

  function isVisible(id) { return !!_active[id]; }

  /* ═══════════════════════════════════════════════════════
     ELEMENT BUILDER
     ═══════════════════════════════════════════════════════ */
  function _buildEl(id, def, data) {
    const el       = document.createElement('div');
    el.className   = `widget widget--${id}`;
    el.id          = `widget-${id}`;
    el.dataset.widgetId = id;
    el.dataset.pinned = 'false';
    el.style.cssText = `opacity:0;transform:scale(0.88) translateY(12px);transition:opacity .38s ease,transform .38s cubic-bezier(.16,1,.3,1);`;
    el.innerHTML   = typeof def.render === 'function' ? def.render(data) : '';

    // Close button (all non-persistent widgets)
    if (!def.persistent) {
      const x      = document.createElement('button');
      x.className  = 'widget-close';
      x.textContent = '×';
      x.addEventListener('click', () => hide(id));
      el.appendChild(x);
    }

    // Pin button
    if (def.pinnable !== false) {
      const pin      = document.createElement('button');
      pin.className  = 'widget-pin';
      pin.textContent = '📌';
      pin.title = 'Pin widget';
      pin.addEventListener('click', (evt) => {
        evt.stopPropagation();
        _togglePin(el, id);
      });
      el.appendChild(pin);
    }

    // Resize handle
    const resizer = document.createElement('div');
    resizer.className = 'widget-resize-handle';
    el.appendChild(resizer);

    // After-build hook
    if (typeof def.mount === 'function') {
      requestAnimationFrame(() => def.mount(el, data));
    }

    return el;
  }

  /* ═══════════════════════════════════════════════════════
     POSITIONING
     ═══════════════════════════════════════════════════════ */
  const _POSITIONS = {
    center:        'top:50%;left:50%;transform:translate(-50%,-50%) scale(0.88)',
    'top-left':    'top:70px;left:280px',
    'top-right':   'top:70px;right:280px',
    'bottom-left': 'bottom:70px;left:280px',
    'bottom-right':'bottom:70px;right:280px',
    'top-center':  'top:80px;left:50%;transform:translateX(-50%) scale(0.88)',
    'bottom-center':'bottom:80px;left:50%;transform:translateX(-50%) scale(0.88)',
  };

  function _positionWidget(el, pos) {
    el.style.position = 'fixed';
    el.style.zIndex   = '90';
    el.style.pointerEvents = 'auto';

    const saved = _layouts[el.dataset.widgetId];
    if (saved && typeof saved === 'object') {
      if (saved.x != null) el.style.left   = `${saved.x}px`;
      if (saved.y != null) el.style.top    = `${saved.y}px`;
      if (saved.width != null)  el.style.width  = `${saved.width}px`;
      if (saved.height != null) el.style.height = `${saved.height}px`;
      el.dataset.pinned = saved.pinned ? 'true' : 'false';
      if (saved.pinned) el.classList.add('widget--pinned');
      return;
    }

    const css = _POSITIONS[pos] || _POSITIONS.center;
    css.split(';').forEach(rule => {
      const [k, v] = rule.split(':');
      if (k && v) el.style[k.trim().replace(/-([a-z])/g, (_, c) => c.toUpperCase())] = v.trim();
    });
  }

  /* ═══════════════════════════════════════════════════════
     INIT — create widget layer, inject CSS, register defaults
     ═══════════════════════════════════════════════════════ */
  function init() {
    _layer           = document.createElement('div');
    _layer.id        = 'widget-layer';
    _layer.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:90;display:block';
    document.body.appendChild(_layer);

    _injectCSS();
    _registerBuiltins();
    _wireWSHandler();
    _wireVoiceCommands();
    _wireModeVisibility();
    restoreLayout();
  }

  /* ═══════════════════════════════════════════════════════
     WIDGET CSS (injected once at runtime)
     ═══════════════════════════════════════════════════════ */
  function _injectCSS() {
    const style = document.createElement('style');
    style.id    = 'widget-engine-styles';
    style.textContent = `
/* ── Widget base ── */
.widget{
  pointer-events:auto;
  background:rgba(2,13,26,.88);
  border:1px solid rgba(0,229,255,.25);
  border-radius:4px;
  padding:16px 18px;
  min-width:240px;
  font-family:'Courier New',monospace;
  font-size:11px;
  color:#e8f4f8;
  letter-spacing:.06em;
  backdrop-filter:blur(14px);
  box-shadow:0 0 30px rgba(0,229,255,.12),inset 0 0 30px rgba(0,229,255,.03);
  position:fixed;
}
.widget-title{
  font-size:9px;letter-spacing:.25em;color:#00e5ff;
  text-shadow:0 0 8px rgba(0,229,255,.5);
  padding-bottom:8px;border-bottom:1px solid rgba(0,229,255,.15);
  margin-bottom:10px;display:flex;align-items:center;gap:8px;
}
.widget-title-icon{font-size:14px}
.widget-close{
  position:absolute;top:8px;right:10px;
  background:none;border:none;color:rgba(232,244,248,.4);
  font-size:16px;cursor:pointer;line-height:1;
  transition:color .2s;font-family:inherit;
}
.widget-close:hover{color:#ff1744}
  .widget-pin{
    position:absolute;top:8px;left:10px;background:none;border:none;color:rgba(232,244,248,.4);
    font-size:14px;cursor:pointer;line-height:1;padding:0;transition:color .2s;font-family:inherit;
  }
  .widget-pin:hover{color:#00e676}
  .widget--pinned{border-color:rgba(0,230,118,.55);box-shadow:0 0 50px rgba(0,230,118,.12),inset 0 0 20px rgba(0,230,118,.05)}
  .widget-resize-handle{
    position:absolute;right:8px;bottom:8px;width:14px;height:14px;
    background:rgba(0,229,255,.18);border:1px solid rgba(0,229,255,.28);border-radius:3px;
    cursor:nwse-resize;box-shadow:0 0 10px rgba(0,229,255,.18);
  }

/* ── Shared widget sub-elements ── */
.widget-row{display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid rgba(0,229,255,.06)}
.widget-row:last-child{border-bottom:none}
.wl{color:rgba(232,244,248,.55);font-size:9px;letter-spacing:.15em}
.wv{color:#e8f4f8;font-size:12px}
.wv--cyan{color:#00e5ff}
.wv--green{color:#00e676}
.wv--warn{color:#ffc400}
.wv--err{color:#ff1744}

.widget-bar-wrap{height:3px;background:rgba(0,229,255,.08);border-radius:1px;overflow:hidden;margin-top:4px}
.widget-bar{height:100%;border-radius:1px;background:linear-gradient(90deg,#1565c0,#00e5ff);box-shadow:0 0 6px rgba(0,229,255,.4);transition:width .6s ease}

/* ── State widget ── */
.widget--state .state-label{font-size:22px;letter-spacing:.3em;color:#00e5ff;text-shadow:0 0 20px rgba(0,229,255,.5);text-align:center;padding:8px 0}
.widget--state .state-icon{font-size:36px;text-align:center;animation:widgetIconPulse 2s ease-in-out infinite}
@keyframes widgetIconPulse{0%,100%{transform:scale(1);opacity:.8}50%{transform:scale(1.08);opacity:1}}

/* ── Weather widget ── */
.widget--weather .weather-temp{font-size:36px;color:#e8f4f8;letter-spacing:.05em}
.widget--weather .weather-icon{font-size:28px;text-align:right}
.widget--weather .weather-row{display:flex;justify-content:space-between;align-items:flex-start}

/* ── Spotify widget ── */
.widget--spotify .spotify-track{font-size:12px;color:#00e5ff;margin-bottom:2px}
.widget--spotify .spotify-artist{font-size:10px;color:rgba(232,244,248,.6)}
.widget--spotify .spotify-progress{height:2px;background:rgba(0,229,255,.12);margin:10px 0 4px;position:relative;border-radius:1px;overflow:hidden}
.widget--spotify .spotify-bar{height:100%;background:#00e5ff;box-shadow:0 0 8px rgba(0,229,255,.6);transition:width .5s linear}
.widget--spotify .spotify-controls{display:flex;gap:8px;margin-top:10px}
.spotify-ctrl-btn{background:rgba(0,229,255,.08);border:1px solid rgba(0,229,255,.2);color:#00e5ff;font-size:14px;width:32px;height:24px;cursor:pointer;border-radius:2px;transition:all .2s;font-family:inherit}
.spotify-ctrl-btn:hover{background:rgba(0,229,255,.2);box-shadow:0 0 8px rgba(0,229,255,.3)}

/* ── Maps widget ── */
.widget--maps{width:320px}
.widget--maps iframe{width:100%;height:200px;border:none;border-radius:2px;margin-top:8px;filter:invert(1) hue-rotate(180deg) brightness(.85) saturate(1.5)}

/* ── Memory widget ── */
.widget--memory .mem-event{font-size:10px;color:rgba(232,244,248,.7);padding:4px 0;border-bottom:1px solid rgba(0,229,255,.06);animation:memEntryIn .3s ease-out}
@keyframes memEntryIn{from{opacity:0;transform:translateX(-6px)}to{opacity:1;transform:translateX(0)}}
.mem-event-tag{font-size:8px;padding:1px 5px;background:rgba(0,229,255,.12);color:#00e5ff;border-radius:2px;margin-right:6px}

/* ── Notification widget ── */
.widget--notification{min-width:280px;border-color:rgba(0,229,255,.35)}
.notif-msg{font-size:12px;color:#e8f4f8;line-height:1.5;padding:4px 0}
.notif-source{font-size:9px;color:rgba(232,244,248,.4);margin-top:6px;letter-spacing:.12em}

/* ── Camera / Vision widget ── */
.widget--camera{width:300px}
.widget--camera video{width:100%;height:180px;object-fit:cover;border-radius:2px;margin-top:8px;border:1px solid rgba(0,229,255,.2)}

/* ── Clipboard widget ── */
.widget--clipboard .clip-text{
  font-size:11px;color:rgba(232,244,248,.85);line-height:1.5;
  max-height:80px;overflow:hidden;padding:6px;
  background:rgba(0,229,255,.03);border:1px solid rgba(0,229,255,.1);
  border-radius:2px;margin-top:6px;word-break:break-all;
}

/* ── Battery widget ── */
.battery-body{display:flex;align-items:center;gap:8px;padding:8px 0}
.battery-icon{font-size:28px}
.battery-pct{font-size:32px;color:#00e676;letter-spacing:.05em}
.battery-pct.low{color:#ffc400} .battery-pct.critical{color:#ff1744}

/* ── Internet widget ── */
.widget--internet .inet-status{font-size:20px;letter-spacing:.2em;text-align:center;padding:6px 0}
.inet-ok{color:#00e676} .inet-fail{color:#ff1744}

/* Entrance/exit */
.widget[data-hiding]{opacity:0!important;transform:scale(.92) translateY(-8px)!important}
`;
    document.head.appendChild(style);
  }

  /* ═══════════════════════════════════════════════════════
     BUILT-IN WIDGET DEFINITIONS
     ═══════════════════════════════════════════════════════ */
  function _registerBuiltins() {

    /* ── WEATHER ── */
    register('weather', {
      position: 'top-right',
      ttl: 30000,
      render: d => `
        <div class="widget-title"><span class="widget-title-icon">◈</span>WEATHER — ${(d.city||'LOCATION').toUpperCase()}</div>
        <div class="weather-row">
          <div>
            <div class="weather-temp">${d.temp ?? '--'}°${d.unit||'C'}</div>
            <div style="font-size:10px;color:rgba(232,244,248,.6);margin-top:2px">${d.condition||'—'}</div>
          </div>
          <div class="weather-icon">${_weatherIcon(d.condition)}</div>
        </div>
        <div style="margin-top:12px">
          <div class="widget-row"><span class="wl">HUMIDITY</span><span class="wv">${d.humidity??'--'}%</span></div>
          <div class="widget-row"><span class="wl">WIND</span><span class="wv">${d.wind??'--'} km/h</span></div>
          <div class="widget-row"><span class="wl">FEELS LIKE</span><span class="wv">${d.feels_like??'--'}°${d.unit||'C'}</span></div>
          <div class="widget-row"><span class="wl">VISIBILITY</span><span class="wv">${d.visibility??'--'} km</span></div>
        </div>`,
    });

    /* ── SPOTIFY ── */
    register('spotify', {
      position: 'bottom-left',
      ttl: 0,
      render: d => `
        <div class="widget-title"><span class="widget-title-icon">♫</span>NOW PLAYING</div>
        <div class="spotify-track" id="sp-track">${_esc(d.track||'—')}</div>
        <div class="spotify-artist" id="sp-artist">${_esc(d.artist||'—')}</div>
        <div class="spotify-progress"><div class="spotify-bar" id="sp-bar" style="width:${d.progress_pct||0}%"></div></div>
        <div style="display:flex;justify-content:space-between;font-size:9px;color:rgba(232,244,248,.4)">
          <span id="sp-elapsed">${_fmtTime(d.elapsed_ms||0)}</span>
          <span id="sp-duration">${_fmtTime(d.duration_ms||0)}</span>
        </div>
        <div class="spotify-controls">
          <button class="spotify-ctrl-btn" id="sp-prev" title="Previous">⏮</button>
          <button class="spotify-ctrl-btn" id="sp-play" title="Play/Pause">${d.is_playing?'⏸':'▶'}</button>
          <button class="spotify-ctrl-btn" id="sp-next" title="Next">⏭</button>
          <button class="spotify-ctrl-btn" id="sp-vol-dn" title="Volume -">🔉</button>
          <button class="spotify-ctrl-btn" id="sp-vol-up" title="Volume +">🔊</button>
        </div>`,
      mount: (el, d) => {
        const cmd = action => window.JARVIS && window.JARVIS.sendWS('spotify_control', { action });
        el.querySelector('#sp-prev').onclick = () => cmd('prev');
        el.querySelector('#sp-play').onclick = () => cmd('toggle');
        el.querySelector('#sp-next').onclick = () => cmd('next');
        el.querySelector('#sp-vol-dn').onclick = () => cmd('vol_down');
        el.querySelector('#sp-vol-up').onclick = () => cmd('vol_up');
      },
      patch: (el, d) => {
        _setText(el, '#sp-track',    d.track||'—');
        _setText(el, '#sp-artist',   d.artist||'—');
        _setText(el, '#sp-elapsed',  _fmtTime(d.elapsed_ms||0));
        _setText(el, '#sp-duration', _fmtTime(d.duration_ms||0));
        const bar = el.querySelector('#sp-bar');
        if (bar) bar.style.width = (d.progress_pct||0) + '%';
        const btn = el.querySelector('#sp-play');
        if (btn) btn.textContent = d.is_playing ? '⏸' : '▶';
      },
    });

    /* ── MEMORY LOG ── */
    register('memory', {
      position: 'top-left',
      ttl: 12000,
      render: d => `
        <div class="widget-title"><span class="widget-title-icon">⬡</span>MEMORY EVENT</div>
        <div id="mem-widget-list"></div>`,
      mount: (el, d) => _appendMemEvent(el, d),
      patch: (el, d) => _appendMemEvent(el, d),
    });

    /* ── NOTIFICATION ── */
    register('notification', {
      position: 'top-right',
      ttl: 6000,
      render: d => `
        <div class="widget-title"><span class="widget-title-icon">◎</span>NOTIFICATION</div>
        <div class="notif-msg">${_esc(d.message||d.text||'')}</div>
        <div class="notif-source">${_esc(d.source||'SYSTEM')}</div>`,
    });

    /* ── BATTERY ── */
    register('battery', {
      position: 'bottom-right',
      ttl: 8000,
      render: d => {
        const pct   = d.level ?? 100;
        const cls   = pct < 20 ? 'critical' : pct < 40 ? 'low' : '';
        const icon  = pct > 80 ? '🔋' : pct > 40 ? '🪫' : '⚠';
        const state = d.charging ? ' ⚡ CHARGING' : '';
        return `
          <div class="widget-title"><span class="widget-title-icon">⌁</span>BATTERY${state}</div>
          <div class="battery-body">
            <span class="battery-icon">${icon}</span>
            <span class="battery-pct ${cls}">${pct}%</span>
          </div>
          <div class="widget-bar-wrap"><div class="widget-bar" style="width:${pct}%;background:${pct<20?'#ff1744':pct<40?'#ffc400':'linear-gradient(90deg,#1565c0,#00e676)'}"></div></div>`;
      },
    });

    /* ── INTERNET ── */
    register('internet', {
      position: 'bottom-right',
      ttl: 6000,
      render: d => `
        <div class="widget-title"><span class="widget-title-icon">◈</span>CONNECTIVITY</div>
        <div class="inet-status ${d.online?'inet-ok':'inet-fail'}">${d.online?'● ONLINE':'● OFFLINE'}</div>
        <div class="widget-row"><span class="wl">LATENCY</span><span class="wv ${d.latency>200?'wv--warn':''}">${d.latency??'--'} ms</span></div>
        <div class="widget-row"><span class="wl">IP</span><span class="wv wv--cyan">${d.ip||'—'}</span></div>`,
    });

    /* ── MAPS ── */
    register('maps', {
      position: 'top-right',
      ttl: 0,
      render: d => {
        const q = encodeURIComponent(d.query || d.location || 'New Delhi, India');
        return `
          <div class="widget-title"><span class="widget-title-icon">◫</span>MAPS — ${(d.location||d.query||'').toUpperCase()}</div>
          <iframe src="https://www.openstreetmap.org/export/embed.html?bbox=&layer=mapnik&marker=&query=${q}" loading="lazy"></iframe>
          <div style="font-size:9px;color:rgba(232,244,248,.4);margin-top:6px">OPENSTREETMAP — STARK GEOLOCATOR</div>`;
      },
    });

    /* ── CLIPBOARD ── */
    register('clipboard', {
      position: 'bottom-left',
      ttl: 10000,
      render: d => `
        <div class="widget-title"><span class="widget-title-icon">▣</span>CLIPBOARD</div>
        <div class="clip-text">${_esc(d.text||'—')}</div>
        <div style="font-size:9px;color:rgba(232,244,248,.4);margin-top:8px">${d.chars??0} CHARS · ${d.words??0} WORDS</div>`,
    });

    /* ── CAMERA FEED ── */
    register('camera', {
      position: 'top-right',
      ttl: 0,
      render: () => `
        <div class="widget-title"><span class="widget-title-icon">◎</span>OPTICAL SENSOR</div>
        <video id="widget-cam-video" autoplay playsinline muted style="width:100%;height:180px;object-fit:cover;border-radius:2px;border:1px solid rgba(0,229,255,.2);margin-top:8px"></video>
        <div style="font-size:9px;color:rgba(0,229,255,.5);margin-top:6px;letter-spacing:.15em">LIVE — FACIAL RECOGNITION IDLE</div>`,
      mount: async (el) => {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ video:true, audio:false });
          const vid    = el.querySelector('#widget-cam-video');
          if (vid) vid.srcObject = stream;
          el._camStream = stream;
        } catch (e) {}
      },
      patch: () => {},
    });

  }  // end _registerBuiltins

  /* ═══════════════════════════════════════════════════════
     WS MESSAGE HANDLER EXTENSION
     Intercepts  { type:"widget", data:{ id, action, ...payload } }
     ═══════════════════════════════════════════════════════ */
  function _wireWSHandler() {
    // Patch into JARVIS WS pipeline via custom event
    document.addEventListener('jarvis:wsRaw', e => {
      const msg = e.detail;
      if (msg.type !== 'widget') return;
      const { id, action, ...payload } = msg.data || {};
      if (!id) return;
      if (action === 'hide')   hide(id);
      else if (action === 'update') update(id, payload);
      else                          show(id, payload);
    });

    // Also react to well-known state changes to auto-show widgets
    document.addEventListener('jarvis:stateChange', e => {
      const s = e.detail;
      if (s === 'speaking' && !isVisible('state')) {
        show('state', { label: 'SPEAKING', icon: '◉', color: '#00e676' });
      } else if (s !== 'speaking') {
        hide('state');
      }
    });
  }

  /* ── Voice-trigger "show maps new delhi", "show weather", etc. ── */
  function _wireVoiceCommands() {
    document.addEventListener('jarvis:userMessage', e => {
      const text = (e.detail || '').toLowerCase();
      if (/show.*(map|location|where)/.test(text) || /maps?\s/.test(text)) {
        const m = text.match(/(?:map|location|navigate to?)\s+(.+)/);
        show('maps', { location: m ? m[1] : '' });
      }
      if (/weather/.test(text)) {
        show('weather', { city: 'Current Location', temp: '--', condition: 'Fetching...' });
        window.JARVIS && window.JARVIS.sendWS('fetch_weather', {});
      }
      if (/clipboard/.test(text)) {
        navigator.clipboard && navigator.clipboard.readText().then(t => {
          show('clipboard', { text: t, chars: t.length, words: t.trim().split(/\s+/).length });
        }).catch(() => {});
      }
      if (/camera|webcam/.test(text)) toggle('camera');
      if (/battery/.test(text)) show('battery', { level: _readBattery() });
    });
  }

  function _wireModeVisibility() {
    document.addEventListener('modeChange', e => {
      const mode = e.detail?.to;
      if (!_layer) return;
      _layer.style.display = mode === 'online' ? 'block' : 'none';
    });
  }

  function _loadLayouts() {
    try {
      const raw = localStorage.getItem(_layoutStoreKey);
      return raw ? JSON.parse(raw) : {};
    } catch (e) {
      return {};
    }
  }

  function _persistLayouts() {
    try {
      localStorage.setItem(_layoutStoreKey, JSON.stringify(_layouts));
    } catch (e) {}
  }

  function _saveLayout(id, state) {
    if (!id) return;
    _layouts[id] = { ...(_layouts[id] || {}), ...state };
    _persistLayouts();
  }

  function _removeLayout(id) {
    delete _layouts[id];
    _persistLayouts();
  }

  function restoreLayout() {
    Object.keys(_layouts).forEach(id => {
      const saved = _layouts[id];
      if (!saved || saved.visible === false) return;
      const def = _registry[id];
      if (!def) return;
      show(id, saved.data || {});
    });
  }

  function _applyLayout(el, saved) {
    if (!el || !saved) return;
    if (saved.x != null) el.style.left   = `${saved.x}px`;
    if (saved.y != null) el.style.top    = `${saved.y}px`;
    if (saved.width != null)  el.style.width  = `${saved.width}px`;
    if (saved.height != null) el.style.height = `${saved.height}px`;
    el.dataset.pinned = saved.pinned ? 'true' : 'false';
    el.classList.toggle('widget--pinned', !!saved.pinned);
  }

  function _togglePin(el, id) {
    const pinned = el.dataset.pinned === 'true';
    const next   = !pinned;
    el.dataset.pinned = next ? 'true' : 'false';
    el.classList.toggle('widget--pinned', next);
    if (next && _active[id]) {
      clearTimeout(_active[id].hideTimer);
      _active[id].hideTimer = null;
    }
    _saveLayout(id, { pinned: next });
  }

  function _setWidgetLayoutFromElement(id, el) {
    const rect = el.getBoundingClientRect();
    _saveLayout(id, {
      x: Math.round(rect.left),
      y: Math.round(rect.top),
      width: Math.round(rect.width),
      height: Math.round(rect.height),
      pinned: el.dataset.pinned === 'true',
    });
  }

  function _snapToEdge(el) {
    const rect = el.getBoundingClientRect();
    const snap = 24;
    let x = parseFloat(el.style.left) || rect.left;
    let y = parseFloat(el.style.top) || rect.top;
    if (x < snap) x = 12;
    if (x + rect.width > window.innerWidth - snap) x = window.innerWidth - rect.width - 12;
    if (y < snap + 58) y = 58;
    if (y + rect.height > window.innerHeight - snap - 40) y = window.innerHeight - rect.height - 12;
    el.style.left = `${Math.max(12, x)}px`;
    el.style.top  = `${Math.max(58, y)}px`;
  }

  function _makeDraggable(el, id) {
    let grabbing = false;
    let startX = 0;
    let startY = 0;
    let originX = 0;
    let originY = 0;

    const onDown = (evt) => {
      if (evt.button !== 0) return;
      if (evt.target.closest('.widget-close') || evt.target.closest('.widget-pin') || evt.target.closest('.widget-resize-handle')) return;
      grabbing = true;
      startX = evt.clientX;
      startY = evt.clientY;
      const rect = el.getBoundingClientRect();
      originX = rect.left;
      originY = rect.top;
      el.style.transition = 'none';
      document.addEventListener('pointermove', onMove);
      document.addEventListener('pointerup', onUp, { once: true });
    };

    const onMove = (evt) => {
      if (!grabbing) return;
      const dx = evt.clientX - startX;
      const dy = evt.clientY - startY;
      const x = Math.round(originX + dx);
      const y = Math.round(originY + dy);
      el.style.left = `${x}px`;
      el.style.top = `${y}px`;
    };

    const onUp = () => {
      if (!grabbing) return;
      grabbing = false;
      el.style.transition = 'opacity .38s ease,transform .38s cubic-bezier(.16,1,.3,1)';
      _snapToEdge(el);
      _setWidgetLayoutFromElement(id, el);
      document.removeEventListener('pointermove', onMove);
    };

    el.addEventListener('pointerdown', onDown);
  }

  function _makeResizable(el, id) {
    const handle = el.querySelector('.widget-resize-handle');
    if (!handle) return;
    let resizing = false;
    let startX = 0;
    let startY = 0;
    let startW = 0;
    let startH = 0;

    const onDown = (evt) => {
      evt.stopPropagation();
      resizing = true;
      startX = evt.clientX;
      startY = evt.clientY;
      startW = el.offsetWidth;
      startH = el.offsetHeight;
      el.style.transition = 'none';
      document.addEventListener('pointermove', onMove);
      document.addEventListener('pointerup', onUp, { once: true });
    };

    const onMove = (evt) => {
      if (!resizing) return;
      const dx = evt.clientX - startX;
      const dy = evt.clientY - startY;
      const width = Math.max(240, startW + dx);
      const height= Math.max(140, startH + dy);
      el.style.width = `${Math.min(width, window.innerWidth - 48)}px`;
      el.style.height = `${Math.min(height, window.innerHeight - 120)}px`;
    };

    const onUp = () => {
      if (!resizing) return;
      resizing = false;
      el.style.transition = 'opacity .38s ease,transform .38s cubic-bezier(.16,1,.3,1)';
      _setWidgetLayoutFromElement(id, el);
      document.removeEventListener('pointermove', onMove);
    };

    handle.addEventListener('pointerdown', onDown);
  }

  function _cleanupWidget(el) {
    if (!el) return;
    if (typeof el._cleanup === 'function') {
      el._cleanup();
      el._cleanup = null;
    }
  }

  function _handleLifecycle(el, id, def, data) {
    _makeDraggable(el, id);
    _makeResizable(el, id);
    if (def.persistent && def.pinnable !== false) {
      el.classList.add('widget--pinned');
      el.dataset.pinned = 'true';
    }
    _saveLayout(id, {
      x: parseInt(el.style.left, 10) || 0,
      y: parseInt(el.style.top, 10) || 0,
      width: parseInt(el.style.width, 10) || el.offsetWidth,
      height: parseInt(el.style.height, 10) || el.offsetHeight,
      pinned: el.dataset.pinned === 'true',
    });
  }

  /* ═══════════════════════════════════════════════════════
     HELPERS
     ═══════════════════════════════════════════════════════ */
  function _appendMemEvent(el, d) {
    const list = el.querySelector('#mem-widget-list');
    if (!list) return;
    const row      = document.createElement('div');
    row.className  = 'mem-event';
    row.innerHTML  = `<span class="mem-event-tag">${_esc(d.type||'MEM')}</span>${_esc(d.content||d.text||'')}`;
    list.appendChild(row);
    if (list.children.length > 5) list.removeChild(list.firstChild);
  }

  function _weatherIcon(cond = '') {
    const c = cond.toLowerCase();
    if (c.includes('rain'))  return '🌧';
    if (c.includes('cloud')) return '⛅';
    if (c.includes('snow'))  return '❄';
    if (c.includes('storm')) return '⛈';
    if (c.includes('sun') || c.includes('clear')) return '☀';
    return '🌡';
  }

  function _fmtTime(ms) {
    const s = Math.floor(ms / 1000);
    return `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;
  }

  function _esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function _setText(root, sel, val) {
    const el = root.querySelector(sel);
    if (el) el.textContent = val;
  }

  function _readBattery() {
    const el = document.getElementById('stat-battery');
    return el ? parseInt(el.textContent) || 100 : 100;
  }

  /* ═══════════════════════════════════════════════════════
     AUTO-INIT on DOMContentLoaded
     ═══════════════════════════════════════════════════════ */
  document.addEventListener('DOMContentLoaded', init);

  /* ═══════════════════════════════════════════════════════
     PUBLIC
     ═══════════════════════════════════════════════════════ */
  return {
    register: register,
    registerWidget: register,
    show: show,
    showWidget: show,
    hide: hide,
    hideWidget: hide,
    update: update,
    toggle: toggle,
    toggleWidget: toggle,
    destroy: destroy,
    destroyWidget: destroy,
    pinWidget: pinWidget,
    saveLayout: saveLayout,
    restoreLayout: restoreLayout,
    isVisible: isVisible,
  };

})();
