/*
============================================================
PROJECT : JARVIS MARK 5
FILE    : server.js
PATH    : hud\websocket\server.js

CHANGES vs original:
  The original file was EMPTY (only had the header comment).
  This is a complete implementation.

PURPOSE :
  WebSocket server bridging Python brain to Electron HUD.
  - Python sends events via HTTP POST to /event (port 8766)
  - This server forwards them to all connected HUD WebSocket clients (port 8765)
  - HUD script.js connects to ws://localhost:8765 (unchanged)

PYTHON USAGE (add to main.py):
  import requests
  def hud_event(event_type, data={}):
      try:
          requests.post("http://localhost:8766/event",
                        json={"type": event_type, "data": data},
                        timeout=0.5)
      except Exception:
          pass

EVENTS PYTHON SENDS:
  hud_event("state",   {"state": "listening"})
  hud_event("stats",   {"cpu": 42, "ram": 61, ...})
  hud_event("message", {"role": "user", "text": "..."})
  hud_event("task",    {"description": "...", "progress": 60})
  hud_event("notification", {"text": "..."})
  hud_event("module",  {"name": "automation", "status": "active"})
============================================================
*/

'use strict';

const WebSocket = require('ws');
const http      = require('http');

const WS_PORT   = 8765;   // HUD connects here
const HTTP_PORT = 8766;   // Python posts events here

// ── Connected HUD clients ──────────────────────────────────────────────────
const clients = new Set();

// ── WebSocket server (HUD side) ────────────────────────────────────────────
const wss = new WebSocket.Server({ port: WS_PORT }, () => {
  console.log(`[WS] J.A.R.V.I.S. WebSocket server online → ws://localhost:${WS_PORT}`);
});

wss.on('connection', (ws, req) => {
  clients.add(ws);
  console.log(`[WS] HUD connected. Total clients: ${clients.size}`);

  // Send ONLINE confirmation immediately on connect
  _send(ws, { type: 'state', data: { state: 'idle' } });
  _send(ws, { type: 'notification', data: { text: 'J.A.R.V.I.S. systems online.' } });

  ws.on('close', () => {
    clients.delete(ws);
    console.log(`[WS] HUD disconnected. Total clients: ${clients.size}`);
  });

  ws.on('error', (err) => {
    console.error(`[WS] Client error: ${err.message}`);
    clients.delete(ws);
  });

  // Forward HUD → Python messages (e.g. spotify_control, widget interactions)
  ws.on('message', (raw) => {
    try {
      const msg = JSON.parse(raw);
      console.log(`[WS] HUD → Python: ${JSON.stringify(msg)}`);
      // Future: forward to Python via a separate IPC channel if needed
    } catch (e) {
      console.error(`[WS] Invalid message from HUD: ${e.message}`);
    }
  });
});

// ── Broadcast to all connected HUD clients ─────────────────────────────────
function broadcast(payload) {
  const raw = JSON.stringify(payload);
  clients.forEach((ws) => {
    if (ws.readyState === WebSocket.OPEN) {
      try {
        ws.send(raw);
      } catch (e) {
        console.error(`[WS] Send error: ${e.message}`);
        clients.delete(ws);
      }
    }
  });
}

function _send(ws, payload) {
  try {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload));
    }
  } catch (e) {
    console.error(`[WS] _send error: ${e.message}`);
  }
}

// ── HTTP event receiver (Python side) ─────────────────────────────────────
const httpServer = http.createServer((req, res) => {
  // CORS headers for any tooling
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.method === 'POST' && req.url === '/event') {
    let body = '';
    req.on('data', (chunk) => { body += chunk; });
    req.on('end', () => {
      try {
        const event = JSON.parse(body);
        // Validate minimum structure
        if (!event.type) throw new Error('Missing event.type');

        console.log(`[HTTP] Python → HUD: type=${event.type}`);
        broadcast(event);

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, clients: clients.size }));
      } catch (e) {
        console.error(`[HTTP] Bad event: ${e.message}`);
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: e.message }));
      }
    });
    return;
  }

  // Health check
  if (req.method === 'GET' && req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status:  'online',
      clients: clients.size,
      ws_port: WS_PORT,
    }));
    return;
  }

  res.writeHead(404);
  res.end('Not found');
});

httpServer.listen(HTTP_PORT, '127.0.0.1', () => {
  console.log(`[HTTP] Event receiver online → http://localhost:${HTTP_PORT}/event`);
});

httpServer.on('error', (err) => {
  console.error(`[HTTP] Server error: ${err.message}`);
});

process.on('uncaughtException', (err) => {
  console.error(`[UNCAUGHT] ${err.message}`);
});

process.on('unhandledRejection', (reason) => {
  console.error(`[UNHANDLED REJECTION] ${reason}`);
});