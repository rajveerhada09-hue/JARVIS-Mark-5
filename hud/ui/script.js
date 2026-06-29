/*
============================================================
PROJECT : JARVIS MARK 5

FILE    : script.js

PATH    : hud\ui\script.js

PURPOSE :
Main Electron HUD frontend logic.

LAST UPDATED :
2026-06-28

============================================================
*/

/**
 * J.A.R.V.I.S. MARK V — CORE RUNTIME
 * ─────────────────────────────────────
 * Single source of truth for:
 *   - WebSocket connection + message routing
 *   - AI state machine
 *   - System stats (real or simulated)
 *   - Clock / uptime
 *   - Boot sequence
 *   - Voice command interception
 *   - window.JARVIS public API
 *
 * WebSocket protocol  →  send JSON from Python:
 *
 *   { "type": "state",         "data": { "state": "listening|thinking|speaking|executing|idle|error|offline" } }
 *   { "type": "stats",         "data": { cpu, ram, ram_used, ram_total, gpu, gpu_name, disk,
 *                                         net_up, net_down, internet, battery, temperature, processes, cpu_cores } }
 *   { "type": "message",       "data": { "role": "user"|"assistant", "text": "..." } }
 *   { "type": "task",          "data": { "description": "...", "progress": 0-100 } }
 *   { "type": "notification",  "data": { "text": "..." } }
 *   { "type": "memory",        "data": { short, long, context, event? } }
 *   { "type": "memory_recall", "data": { query, results: [{content, score}] } }
 *   { "type": "user_profile",  "data": { name, mode, projects, preferences } }
 *   { "type": "module",        "data": { "name": "automation", "status": "active|idle|offline|error" } }
 *   { "type": "active_module", "data": { "name": "LLM CORE" } }
 *   { "type": "widget",        "data": { "id": "weather", "action": "show|hide|update", ...payload } }
 *   { "type": "spotify",       "data": { track, artist, progress_pct, elapsed_ms, duration_ms, is_playing } }
 *   { "type": "command",       "data": { "action": "workspace|wakeup|mode", "mode"? } }
 *   { "type": "error",         "data": { "message": "..." } }
 */

'use strict';

/* ══════════════════════════════════════════════════════════════
   CONFIG
   ══════════════════════════════════════════════════════════════ */
const CONFIG = {
  WS_URL:             'ws://localhost:8765',
  WS_RECONNECT_MS:    3000,
  STATS_INTERVAL_MS:  2000,

  BOOT_STEPS: [
    { text: 'INITIALIZING CORE SYSTEMS...',    pct: 8   },
    { text: 'LOADING NEURAL INTERFACE...',     pct: 22  },
    { text: 'CALIBRATING SENSOR ARRAYS...',    pct: 38  },
    { text: 'ESTABLISHING SECURE CHANNEL...',  pct: 54  },
    { text: 'MOUNTING MEMORY SUBSYSTEMS...',   pct: 70  },
    { text: 'SYNCING KNOWLEDGE BASE...',       pct: 84  },
    { text: 'ALL SYSTEMS NOMINAL.',            pct: 100 },
  ],

  /* Voice triggers — matched against every user message */
  TRIGGERS: {
    standby:   [
      /jarvis.*(going out|i'?m? out|leaving|standby|stand by|be back|brb|stepping out)/i,
      /^standby$/i, /^offline(\s+mode)?$/i, /i'?m? going out/i, /i'?ll? be back/i,
    ],
    wakeup: [
      /i'?m? (back|home)/i,
      /jarvis.*(wake up|online|resume|i'?m? back|i'?m? home)/i,
      /^wake up(\s+jarvis)?$/i, /^(jarvis\s+)?online$/i, /^resume$/i,
    ],
    workspace: [ /open workspace/i, /workspace on/i, /start workspace/i ],
    spotify:   [ /play\s+spotify/i, /open\s+spotify/i, /play\s+music/i ],
    weather:   [ /weather/i, /temperature outside/i ],
    maps:      [ /show.*(map|location)/i, /navigate to/i, /where is/i ],
    camera:    [ /open camera/i, /show camera/i, /webcam/i ],
    clipboard: [ /clipboard/i, /what did i copy/i ],
  },
};

/* ══════════════════════════════════════════════════════════════
   RUNTIME STATE
   ══════════════════════════════════════════════════════════════ */
const STATE = {
  aiState:       'idle',
  queryCount:    0,
  startTime:     Date.now(),
  wsConnected:   false,
  ws:            null,
  waveAnimId:    null,
  wavePhase:     0,
  hasRealStats:  false,   // true once WS delivers stats → simulation stops
  _lastState:    'idle',  // for resume after mode change
};

/* ══════════════════════════════════════════════════════════════
   DOM CACHE
   ══════════════════════════════════════════════════════════════ */
const $  = id => document.getElementById(id);
const DOM = {
  body:           document.body,
  bootOverlay:    $('boot-overlay'),
  bootBar:        $('boot-bar'),
  bootStatus:     $('boot-status'),
  timeHH:         $('time-hh'),
  timeMM:         $('time-mm'),
  timeSS:         $('time-ss'),
  dateDisp:       $('date-display'),
  connStatus:     $('connection-status'),
  wsStatus:       $('ws-status'),
  statusLabel:    $('status-label'),
  activeModule:   $('active-module-label'),
  currentTask:    $('current-task'),
  taskFill:       $('task-progress-fill'),
  convLog:        $('conversation-log'),
  cpuArc:         $('cpu-arc'),
  cpuVal:         $('cpu-val'),
  cpuBar:         $('cpu-bar'),
  cpuSub:         $('cpu-sub'),
  ramArc:         $('ram-arc'),
  ramVal:         $('ram-val'),
  ramBar:         $('ram-bar'),
  ramSub:         $('ram-sub'),
  gpuArc:         $('gpu-arc'),
  gpuVal:         $('gpu-val'),
  gpuBar:         $('gpu-bar'),
  gpuSub:         $('gpu-sub'),
  diskC:          $('disk-c'),
  diskCVal:       $('disk-c-val'),
  netUp:          $('net-up'),
  netDown:        $('net-down'),
  netInet:        $('net-inet'),
  battery:        $('stat-battery'),
  uptime:         $('stat-uptime'),
  queries:        $('stat-queries'),
  temp:           $('stat-temp'),
  notifList:      $('notif-list'),
  lastCmd:        $('last-cmd'),
  procCount:      $('proc-count'),
  waveCanvas:     $('waveform-canvas'),
  particleCanvas: $('particle-canvas'),
};

/* ══════════════════════════════════════════════════════════════
   BOOT SEQUENCE
   ══════════════════════════════════════════════════════════════ */
async function runBootSequence() {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < CONFIG.BOOT_STEPS.length; i++) {
    DOM.bootStatus.textContent = CONFIG.BOOT_STEPS[i].text;
    DOM.bootBar.style.width    = CONFIG.BOOT_STEPS[i].pct + '%';

    // If this step references memory sync, wait briefly for the backend
    // to mark mem0 as ready (`data-mem0-ready="true"`) before proceeding.
    if (/SYNC|MEMORY/i.test(CONFIG.BOOT_STEPS[i].text)) {
      const deadline = Date.now() + 5000; // wait up to 5s
      while (DOM.body.dataset.mem0Ready !== 'true' && Date.now() < deadline) {
        await sleep(300);
      }
      if (DOM.body.dataset.mem0Ready === 'true') {
        DOM.bootStatus.textContent = 'MEMORY SUBSYSTEM READY.';
        DOM.bootBar.style.width    = CONFIG.BOOT_STEPS[i].pct + '%';
      }
    }

    await sleep(i === CONFIG.BOOT_STEPS.length - 1 ? 500 : 300);
  }
  await sleep(600);
  DOM.bootOverlay.classList.add('hidden');
  DOM.bootOverlay.addEventListener('transitionend', () => {
    DOM.bootOverlay.style.display = 'none';
  }, { once: true });
}

/* ══════════════════════════════════════════════════════════════
   CLOCK
   ══════════════════════════════════════════════════════════════ */
const DAYS   = ['SUNDAY','MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY'];
const MONTHS = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
const _pad   = n => String(n).padStart(2, '0');

function _updateClock() {
  const n = new Date();
  DOM.timeHH.textContent  = _pad(n.getHours());
  DOM.timeMM.textContent  = _pad(n.getMinutes());
  DOM.timeSS.textContent  = _pad(n.getSeconds());
  DOM.dateDisp.textContent =
    `${DAYS[n.getDay()]} — ${_pad(n.getDate())} ${MONTHS[n.getMonth()]} ${n.getFullYear()}`;
}

function _updateUptime() {
  const e = Math.floor((Date.now() - STATE.startTime) / 1000);
  DOM.uptime.textContent = `${_pad(Math.floor(e/3600))}:${_pad(Math.floor((e%3600)/60))}:${_pad(e%60)}`;
}

/* ══════════════════════════════════════════════════════════════
   AI STATE MACHINE
   ══════════════════════════════════════════════════════════════ */
const STATE_LABELS = {
  idle: 'IDLE', listening: 'LISTENING', thinking: 'THINKING',
  speaking: 'SPEAKING', executing: 'EXECUTING',
  error: 'ERROR', offline: 'OFFLINE',
};

/* State → notification text for the bottom bar */
const STATE_NOTIFICATIONS = {
  listening: 'Voice recognition active.',
  thinking:  'Neural inference in progress...',
  speaking:  'Voice output active.',
  executing: 'Executing command sequence.',
  idle:      'All systems nominal.',
  error:     '⚠ System error detected.',
  offline:   'Connection lost — retrying...',
};

function setAIState(newState) {
  if (newState === STATE.aiState && newState !== 'idle') return; // debounce same-state spam
  STATE._lastState = STATE.aiState;
  STATE.aiState    = newState;

  DOM.body.dataset.state      = newState;
  DOM.statusLabel.textContent = STATE_LABELS[newState] || newState.toUpperCase();

  // Waveform control
  if (newState === 'listening' || newState === 'speaking') {
    _startWaveform();
  } else {
    _stopWaveform();
  }

  // Bottom notification
  const msg = STATE_NOTIFICATIONS[newState];
  if (msg) pushNotification(msg);

  // Reactor speed hint via CSS class
  DOM.body.dataset.reactorSpeed = (newState === 'thinking') ? 'fast'
    : (newState === 'listening') ? 'medium' : 'normal';

  document.dispatchEvent(new CustomEvent('jarvis:stateChange', { detail: newState }));
}

/* ══════════════════════════════════════════════════════════════
   ACTIVE MODULE LABEL (top-right)
   ══════════════════════════════════════════════════════════════ */
function setActiveModule(name) {
  if (!DOM.activeModule) return;
  DOM.activeModule.textContent = name ? `MODULE: ${name.toUpperCase()}` : 'MODULE: —';
  DOM.activeModule.style.opacity = name ? '1' : '0.4';
}

/* ══════════════════════════════════════════════════════════════
   WAVEFORM
   ══════════════════════════════════════════════════════════════ */
function _startWaveform() {
  if (STATE.waveAnimId) return;
  const canvas = DOM.waveCanvas;
  const ctx    = canvas.getContext('2d');

  function _draw() {
    STATE.waveAnimId = requestAnimationFrame(_draw);
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const isSpeaking = STATE.aiState === 'speaking';
    const color = isSpeaking ? '#00e676' : '#40c4ff';
    const amp   = isSpeaking ? 22 : 12;
    const W = canvas.width, H = canvas.height, cx = H / 2;

    // Primary wave
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth   = 1.5;
    ctx.shadowColor = color;
    ctx.shadowBlur  = 10;
    for (let x = 0; x < W; x++) {
      const t = x / W;
      const y = cx
        + Math.sin(t * Math.PI * 12 + STATE.wavePhase) * amp
        + Math.sin(t * Math.PI * 7  + STATE.wavePhase * 1.3) * amp * 0.5
        + Math.sin(t * Math.PI * 20 + STATE.wavePhase * 0.7) * amp * 0.25;
      x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Mirror ghost
    ctx.beginPath();
    ctx.globalAlpha = 0.22;
    for (let x = 0; x < W; x++) {
      const t = x / W;
      const y = cx - (Math.sin(t * Math.PI * 12 + STATE.wavePhase) * amp
                    + Math.sin(t * Math.PI * 7  + STATE.wavePhase * 1.3) * amp * 0.5);
      x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.globalAlpha = 1;

    STATE.wavePhase += isSpeaking ? 0.11 : 0.07;
  }
  _draw();
}

function _stopWaveform() {
  if (STATE.waveAnimId) {
    cancelAnimationFrame(STATE.waveAnimId);
    STATE.waveAnimId = null;
  }
  const ctx = DOM.waveCanvas.getContext('2d');
  ctx.clearRect(0, 0, DOM.waveCanvas.width, DOM.waveCanvas.height);
}

/* ══════════════════════════════════════════════════════════════
   PARTICLE BACKGROUND
   ══════════════════════════════════════════════════════════════ */
function _initParticles() {
  const canvas = DOM.particleCanvas;
  const ctx    = canvas.getContext('2d');
  const resize = () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; };
  resize();
  window.addEventListener('resize', resize);

  const pts = Array.from({ length: 80 }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    r: Math.random() * 1.2 + 0.3,
    vx:(Math.random()-0.5)*0.25,
    vy:(Math.random()-0.5)*0.25,
    a: Math.random(),
    da:(Math.random()-0.5)*0.008,
  }));

  (function _draw() {
    requestAnimationFrame(_draw);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    pts.forEach(p => {
      p.x += p.vx; p.y += p.vy; p.a += p.da;
      if (p.a < 0.05) p.da = Math.abs(p.da);
      if (p.a > 0.80) p.da = -Math.abs(p.da);
      if (p.x < 0) p.x = canvas.width;  if (p.x > canvas.width)  p.x = 0;
      if (p.y < 0) p.y = canvas.height; if (p.y > canvas.height) p.y = 0;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI*2);
      ctx.fillStyle = `rgba(0,229,255,${p.a*0.6})`;
      ctx.fill();
    });
    // Connect nearby particles
    for (let i = 0; i < pts.length; i++) {
      for (let j = i+1; j < pts.length; j++) {
        const dx = pts[i].x-pts[j].x, dy = pts[i].y-pts[j].y;
        const d  = Math.sqrt(dx*dx+dy*dy);
        if (d < 100) {
          ctx.beginPath();
          ctx.strokeStyle = `rgba(0,229,255,${(1-d/100)*0.07})`;
          ctx.lineWidth   = 0.5;
          ctx.moveTo(pts[i].x, pts[i].y);
          ctx.lineTo(pts[j].x, pts[j].y);
          ctx.stroke();
        }
      }
    }
  })();
}

/* ══════════════════════════════════════════════════════════════
   GAUGE HELPER  (r=32 → circumference ≈ 201)
   ══════════════════════════════════════════════════════════════ */
const _CIRC = 2 * Math.PI * 32;

function _setGauge(arcEl, valEl, barEl, pct) {
  const c = Math.max(0, Math.min(100, pct));
  arcEl.style.strokeDasharray = `${(c/100)*_CIRC} ${_CIRC}`;
  valEl.textContent = Math.round(c) + '%';
  barEl.style.width = c + '%';
}

/* ══════════════════════════════════════════════════════════════
   SYSTEM STATS
   ══════════════════════════════════════════════════════════════ */
function applySystemStats(d) {
  if (d.cpu != null)  _setGauge(DOM.cpuArc, DOM.cpuVal, DOM.cpuBar, d.cpu);
  if (d.cpu_cores)    DOM.cpuSub.textContent = `${d.cpu_cores} cores active`;
  if (d.ram != null)  _setGauge(DOM.ramArc, DOM.ramVal, DOM.ramBar, d.ram);
  if (d.ram_used != null && d.ram_total != null)
    DOM.ramSub.textContent = `${(+d.ram_used).toFixed(1)} GB / ${(+d.ram_total).toFixed(1)} GB`;
  if (d.gpu != null)  _setGauge(DOM.gpuArc, DOM.gpuVal, DOM.gpuBar, d.gpu);
  if (d.gpu_name && DOM.gpuSub) DOM.gpuSub.textContent = d.gpu_name;
  if (d.disk != null) { DOM.diskC.style.width = d.disk+'%'; DOM.diskCVal.textContent = Math.round(d.disk)+'%'; }
  if (d.net_up   != null) DOM.netUp.textContent   = _fmtBytes(d.net_up)   + '/s';
  if (d.net_down != null) DOM.netDown.textContent = _fmtBytes(d.net_down)  + '/s';
  if (d.internet != null) {
    DOM.netInet.textContent = d.internet ? 'CONNECTED' : 'OFFLINE';
    DOM.netInet.style.color = d.internet ? 'var(--c-ram)' : 'var(--c-error)';
  }
  if (d.battery     != null) DOM.battery.textContent   = Math.round(d.battery) + '%';
  if (d.temperature != null) DOM.temp.textContent      = d.temperature + '°C';
  if (d.processes   != null) DOM.procCount.textContent = d.processes + ' active';

  // Forward to Processor Mode (if open)
  if (window.ProcessorMode) window.ProcessorMode.applyStats(d);
}

function _fmtBytes(b) {
  if (b == null) return '--';
  if (b < 1024)    return b.toFixed(0)        + ' B';
  if (b < 1048576) return (b/1024).toFixed(1) + ' KB';
  return (b/1048576).toFixed(1) + ' MB';
}

/* Simulation — stops the moment real WS stats arrive */
let _simCPU = 14, _simRAM = 42;
function _simulateStats() {
  if (STATE.hasRealStats) return;
  _simCPU = Math.max(5,  Math.min(95, _simCPU + (Math.random()-0.48)*6));
  _simRAM = Math.max(20, Math.min(90, _simRAM + (Math.random()-0.49)*2));
  applySystemStats({
    cpu: _simCPU, cpu_cores: 8,
    ram: _simRAM, ram_used:(_simRAM/100*16).toFixed(1), ram_total:16,
    disk: 55,
    net_up: Math.random()*50000,
    net_down: Math.random()*200000,
    internet: true,
    battery: 87,
    temperature: 48 + Math.floor(Math.random()*8),
    processes: 140 + Math.floor(Math.random()*40),
  });
}

/* ══════════════════════════════════════════════════════════════
   CONVERSATION LOG
   ══════════════════════════════════════════════════════════════ */
function addLogEntry(tag, text, type) {
  const el       = document.createElement('div');
  el.className   = `log-entry log-entry--${type}`;
  el.innerHTML   = `<span class="log-tag">${tag}</span><span class="log-text">${_esc(text)}</span>`;
  DOM.convLog.appendChild(el);
  DOM.convLog.scrollTop = DOM.convLog.scrollHeight;
  while (DOM.convLog.children.length > 60)
    DOM.convLog.removeChild(DOM.convLog.firstChild);
}

function _esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

/* ══════════════════════════════════════════════════════════════
   NOTIFICATIONS (bottom bar ticker)
   ══════════════════════════════════════════════════════════════ */
function pushNotification(text) {
  const el       = document.createElement('span');
  el.className   = 'notif-item';
  el.textContent = text;
  DOM.notifList.innerHTML = '';
  DOM.notifList.appendChild(el);
}

/* ══════════════════════════════════════════════════════════════
   BATTERY (native browser API — supplements WS data)
   ══════════════════════════════════════════════════════════════ */
function _initBattery() {
  if (!('getBattery' in navigator)) return;
  navigator.getBattery().then(bat => {
    const upd = () => {
      const pct = Math.round(bat.level * 100);
      DOM.battery.textContent = pct + '%';
      // Show widget if low
      if (pct <= 20 && window.WidgetEngine) {
        window.WidgetEngine.show('battery', { level: pct, charging: bat.charging, ttl: 10000 });
      }
    };
    upd();
    bat.addEventListener('levelchange', upd);
    bat.addEventListener('chargingchange', upd);
  }).catch(() => {});
}

/* ══════════════════════════════════════════════════════════════
   VOICE COMMAND ROUTER
   ══════════════════════════════════════════════════════════════ */
function _routeVoiceCommand(text) {
  const TM = window.TransitionManager;

  /* Mode switches */
  if (TM) {
    if (CONFIG.TRIGGERS.standby.some(r => r.test(text)) && TM.currentMode !== 'standby') {
      const secs = _parseDuration(text);
      TM.switchTo('standby', { countdownSecs: secs });
      return;
    }
    if (CONFIG.TRIGGERS.wakeup.some(r => r.test(text)) && TM.currentMode === 'standby') {
      TM.switchTo('online');
      _triggerWakeUp();
      return;
    }
  }

  /* Feature triggers */
  if (CONFIG.TRIGGERS.workspace.some(r => r.test(text))) { _triggerWorkspace(); return; }
  if (CONFIG.TRIGGERS.weather.some(r => r.test(text)))   { sendWS('fetch_weather', {}); return; }
  if (CONFIG.TRIGGERS.maps.some(r => r.test(text))) {
    const m = text.match(/(?:navigate to?|where is|show.+?(?:map|location)(?:\s+(?:of|for))?)\s+(.+)/i);
    if (window.WidgetEngine) window.WidgetEngine.show('maps', { location: m ? m[1] : '' });
    return;
  }
  if (CONFIG.TRIGGERS.camera.some(r => r.test(text)))    { if (window.WidgetEngine) window.WidgetEngine.toggle('camera'); return; }
  if (CONFIG.TRIGGERS.clipboard.some(r => r.test(text))) {
    navigator.clipboard && navigator.clipboard.readText().then(t => {
      if (window.WidgetEngine) window.WidgetEngine.show('clipboard', {
        text: t, chars: t.length, words: t.trim().split(/\s+/).length
      });
    }).catch(() => {});
  }
}

function _parseDuration(text) {
  const m = text.match(/(\d+)\s*(minute|min|hour|hr|second|sec)/i);
  if (!m) return null;
  const n = parseInt(m[1]), u = m[2].toLowerCase();
  if (u.startsWith('hour') || u.startsWith('hr')) return n * 3600;
  if (u.startsWith('min'))  return n * 60;
  return n;
}

/* ══════════════════════════════════════════════════════════════
   WORKSPACE COMMAND
   ══════════════════════════════════════════════════════════════ */
function _triggerWorkspace() {
  setAIState('executing');
  addLogEntry('SYS', 'Workspace command — launching VS Code, Claude, Chrome.', 'system');
  pushNotification('WORKSPACE: Opening development environment...');

  if (window.electronAPI && window.electronAPI.openWorkspace) {
    window.electronAPI.openWorkspace();
    return;
  }
  sendWS('command', {
    action:      'workspace',
    apps:        ['vscode', 'claude'],
    chrome_tabs: [
      'https://chat.openai.com',
      'https://grok.x.com',
      'https://www.perplexity.ai',
    ],
  });
}

/* ══════════════════════════════════════════════════════════════
   WAKE-UP SEQUENCE
   ══════════════════════════════════════════════════════════════ */
function _triggerWakeUp() {
  addLogEntry('SYS', 'Wake-up sequence initiated.', 'system');
  pushNotification('WAKE-UP: Reactivating all systems...');

  if (window.electronAPI && window.electronAPI.playSpotify) {
    window.electronAPI.playSpotify('39shmbIHICJ2Wxnk1fPSdz');
    return;
  }
  sendWS('command', {
    action:   'spotify',
    track_id: '39shmbIHICJ2Wxnk1fPSdz',
    volume:   25,
    minimize: true,
  });
}

/* ══════════════════════════════════════════════════════════════
   WEBSOCKET
   ══════════════════════════════════════════════════════════════ */
function connectWS() {
  if (STATE.ws) { try { STATE.ws.close(); } catch(e) {} }
  let ws;
  try { ws = new WebSocket(CONFIG.WS_URL); }
  catch(e) { _scheduleReconnect(); return; }
  STATE.ws = ws;

  ws.addEventListener('open', () => {
    STATE.wsConnected              = true;
    DOM.wsStatus.textContent       = 'WS CONNECTED';
    DOM.wsStatus.style.color       = 'var(--c-cyan)';
    DOM.connStatus.textContent     = '● ONLINE';
    DOM.connStatus.className       = 'badge badge--online';
    DOM.connStatus.style.color     = '';
    if (STATE.aiState === 'offline') setAIState('idle');
  });

  ws.addEventListener('close',   () => { STATE.wsConnected = false; DOM.wsStatus.textContent = 'WS DISCONNECTED'; DOM.wsStatus.style.color = 'var(--c-error)'; _scheduleReconnect(); });
  ws.addEventListener('error',   () => ws.close());
  ws.addEventListener('message', evt => {
    let msg;
    try { msg = JSON.parse(evt.data); } catch(e) { return; }
    // Broadcast raw for widget engine and other listeners
    document.dispatchEvent(new CustomEvent('jarvis:wsRaw', { detail: msg }));
    _handleWS(msg);
  });
}

function _scheduleReconnect() {
  setAIState('offline');
  DOM.connStatus.textContent  = '● OFFLINE';
  DOM.connStatus.className    = 'badge';
  DOM.connStatus.style.color  = 'var(--c-error)';
  setTimeout(connectWS, CONFIG.WS_RECONNECT_MS);
}

function _handleWS({ type, data }) {
  switch (type) {

    case 'state':
      setAIState(data.state || 'idle');
      break;

    case 'stats':
      STATE.hasRealStats = true;
      applySystemStats(data);
      break;

    case 'message':
      if (data.role === 'user') {
        addLogEntry('YOU', data.text, 'user');
        DOM.lastCmd.textContent = data.text;
        STATE.queryCount++;
        DOM.queries.textContent = String(STATE.queryCount);
        _routeVoiceCommand(data.text);
        document.dispatchEvent(new CustomEvent('jarvis:userMessage', { detail: data.text }));
      } else if (data.role === 'assistant') {
        addLogEntry('AI', data.text, 'ai');
      }
      break;

    case 'task':
      DOM.currentTask.textContent = data.description || 'Processing...';
      DOM.taskFill.style.width    = (data.progress || 0) + '%';
      break;

    case 'notification':
      pushNotification(data.text || '');
      if (window.WidgetEngine) {
        window.WidgetEngine.show('notification', {
          message: data.text,
          source:  data.source || 'SYSTEM',
          ttl:     data.ttl || 6000,
        });
      }
      break;

    case 'memory':
      // Route to MemoryHUD (handles bars + event log + widget)
      if (window.MemoryHUD) window.MemoryHUD.applyMemoryUpdate(data);
      else {
        // Fallback: direct bar update
        const fills = document.querySelectorAll('.mem-fill');
        const vals  = document.querySelectorAll('.mem-val');
        if (fills[0] && data.short   != null) { fills[0].style.width = data.short   + '%'; vals[0].textContent = data.short   + '%'; }
        if (fills[1] && data.long    != null) { fills[1].style.width = data.long    + '%'; vals[1].textContent = data.long    + '%'; }
        if (fills[2] && data.context != null) { fills[2].style.width = data.context + '%'; vals[2].textContent = data.context + '%'; }
      }
      break;

    case 'memory_recall':
      if (window.MemoryHUD) window.MemoryHUD.applyRecall(data);
      break;

    case 'user_profile':
      if (window.MemoryHUD) window.MemoryHUD.applyUserProfile(data);
      break;

    case 'module':
      if (window.ProcessorMode) window.ProcessorMode.setModuleStatus(data.name, data.status);
      break;

    case 'active_module':
      setActiveModule(data.name);
      break;

    case 'widget':
      // Forwarded via jarvis:wsRaw to WidgetEngine — handled there
      break;

    case 'spotify':
      if (window.WidgetEngine) {
        window.WidgetEngine.show('spotify', data);   // show() calls patch() if already open
      }
      break;

    case 'command':
      if (data.action === 'wakeup')    _triggerWakeUp();
      if (data.action === 'workspace') _triggerWorkspace();
      if (data.action === 'mode' && window.TransitionManager)
        window.TransitionManager.switchTo(data.mode);
      break;

    case 'error':
      setAIState('error');
      addLogEntry('ERR', data.message || 'System error', 'system');
      pushNotification('⚠ ERROR: ' + (data.message || 'Unknown error'));
      setTimeout(() => { if (STATE.aiState === 'error') setAIState('idle'); }, 4000);
      break;
  }
}

function sendWS(type, data) {
  if (STATE.ws && STATE.ws.readyState === WebSocket.OPEN) {
    STATE.ws.send(JSON.stringify({ type, data }));
  }
}

/* ══════════════════════════════════════════════════════════════
   ELECTRON BRIDGE
   ══════════════════════════════════════════════════════════════ */
function _initElectronBridge() {
  if (!window.electronAPI) return;
  if (window.electronAPI.onAIState)
    window.electronAPI.onAIState((_e, s) => setAIState(s));
  if (window.electronAPI.onStats)
    window.electronAPI.onStats((_e, d) => { STATE.hasRealStats = true; applySystemStats(d); });
  if (window.electronAPI.onMessage)
    window.electronAPI.onMessage((_e, d) => {
      addLogEntry(d.role === 'user' ? 'YOU' : 'AI', d.text, d.role === 'user' ? 'user' : 'ai');
      if (d.role === 'user') {
        DOM.lastCmd.textContent = d.text;
        STATE.queryCount++;
        DOM.queries.textContent = String(STATE.queryCount);
        _routeVoiceCommand(d.text);
        document.dispatchEvent(new CustomEvent('jarvis:userMessage', { detail: d.text }));
      }
    });
}

/* ══════════════════════════════════════════════════════════════
   INIT
   ══════════════════════════════════════════════════════════════ */
function _init() {
  _initParticles();
  _updateClock();
  setInterval(_updateClock, 1000);
  setInterval(_updateUptime, 1000);
  setInterval(_simulateStats, CONFIG.STATS_INTERVAL_MS);
  _initBattery();
  _initElectronBridge();
  // Hooks: listen for backend mem0 readiness and TTS lifecycle events.
  document.addEventListener('jarvis:wsRaw', (e) => {
    const msg = e.detail;
    if (!msg) return;
    // When the memory module reports active, mark mem0 ready so boot can proceed.
    if (msg.type === 'module' && msg.data && msg.data.name === 'memory' && msg.data.status === 'active') {
      document.body.dataset.mem0Ready = 'true';
    }
    // Some backends may emit a 'memory' payload with a synced flag.
    if (msg.type === 'memory' && msg.data && (msg.data.synced === true || msg.data.synced === 'true')) {
      document.body.dataset.mem0Ready = 'true';
    }
  });
  document.addEventListener('jarvis:ttsStart', () => setAIState('speaking'));
  document.addEventListener('jarvis:ttsEnd',   () => setAIState('idle'));
  connectWS();
  runBootSequence();
  setAIState('idle');
}

document.addEventListener('DOMContentLoaded', _init);

/* ══════════════════════════════════════════════════════════════
   PUBLIC API  window.JARVIS
   ══════════════════════════════════════════════════════════════ */
window.JARVIS = {
  setState:         setAIState,
  applyStats:       applySystemStats,
  addLog:           addLogEntry,
  notify:           pushNotification,
  setActiveModule,
  sendWS,
  triggerWorkspace: _triggerWorkspace,
  triggerWakeUp:    _triggerWakeUp,
  /* Expose STATE read-only for other modules */
  get _lastState()  { return STATE._lastState; },
};  