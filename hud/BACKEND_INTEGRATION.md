/*
============================================================
PROJECT : JARVIS MARK 5

FILE    : BACKEND_INTEGRATION.md

PATH    : hud\BACKEND_INTEGRATION.md

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
*/

# J.A.R.V.I.S. Mark V — Backend ↔ HUD Integration Reference

## WebSocket Server (websocket/server.js or Python equivalent)
Port: **8765**

---

## Message Protocol

All messages are JSON objects: `{ "type": "...", "data": { ... } }`

### State Updates
```json
{ "type": "state", "data": { "state": "idle|listening|thinking|speaking|executing|error|offline" } }
```

### System Stats (send every 2 seconds from Python psutil)
```json
{
  "type": "stats",
  "data": {
    "cpu": 42,
    "cpu_cores": 8,
    "ram": 61,
    "ram_used": 9.8,
    "ram_total": 16,
    "gpu": 34,
    "gpu_name": "RTX 3080",
    "disk": 55,
    "net_up": 12000,
    "net_down": 80000,
    "internet": true,
    "battery": 87,
    "temperature": 52,
    "processes": 168
  }
}
```

### Conversation
```json
{ "type": "message", "data": { "role": "user", "text": "What time is it?" } }
{ "type": "message", "data": { "role": "assistant", "text": "It's 14:30, sir." } }
```

### Task Progress
```json
{ "type": "task", "data": { "description": "Searching the web...", "progress": 60 } }
```

### Memory (MemoryHUD)
```json
{
  "type": "memory",
  "data": {
    "short": 45,
    "long": 72,
    "context": 30,
    "event": {
      "type": "SAVE",
      "content": "User prefers dark theme",
      "importance": 0.85
    }
  }
}
```

### Memory Recall (Mem0 results)
```json
{
  "type": "memory_recall",
  "data": {
    "query": "user preferences",
    "results": [
      { "content": "User prefers dark theme", "score": 0.94, "source": "long" },
      { "content": "User dislikes loud notifications", "score": 0.81, "source": "long" }
    ]
  }
}
```

### User Profile / Personality Mode
```json
{
  "type": "user_profile",
  "data": {
    "name": "Sir",
    "mode": "friendly",
    "projects": ["JARVIS", "ML Pipeline"],
    "preferences": { "theme": "dark", "language": "hinglish" }
  }
}
```

### Module Status
```json
{ "type": "module",        "data": { "name": "automation", "status": "active|idle|offline|error" } }
{ "type": "active_module", "data": { "name": "LLM CORE" } }
```

### Widgets
```json
{ "type": "widget", "data": { "id": "weather", "action": "show", "city": "Delhi", "temp": 28, "condition": "Sunny", "humidity": 65, "wind": 12 } }
{ "type": "widget", "data": { "id": "spotify", "action": "show", "track": "Arc Reactor", "artist": "Hans Zimmer", "progress_pct": 42, "is_playing": true } }
{ "type": "widget", "data": { "id": "weather", "action": "hide" } }
{ "type": "widget", "data": { "id": "weather", "action": "update", "temp": 29 } }
```

### Spotify (live track updates)
```json
{
  "type": "spotify",
  "data": {
    "track": "Iron Man Theme",
    "artist": "Brian Tyler",
    "progress_pct": 35,
    "elapsed_ms": 45000,
    "duration_ms": 128000,
    "is_playing": true
  }
}
```

### Commands (backend → frontend)
```json
{ "type": "command", "data": { "action": "wakeup" } }
{ "type": "command", "data": { "action": "workspace" } }
{ "type": "command", "data": { "action": "mode", "mode": "standby" } }
```

---

## Mem0 Integration Points (memory.py)

```python
# When you add Mem0:
import mem0

client = mem0.MemoryClient(api_key="...")   # or local mode

# On important fact → save + notify HUD
def save_memory(content, importance=0.5, user_id="jarvis_user"):
    client.add(content, user_id=user_id)
    ws_send("memory", {
        "event": { "type": "SAVE", "content": content, "importance": importance }
    })

# On semantic query → search + notify HUD
def recall_memory(query, user_id="jarvis_user"):
    results = client.search(query, user_id=user_id, limit=5)
    ws_send("memory_recall", { "query": query, "results": results })
    return results
```

---

## Voice Command → HUD Triggers (handled in script.js, no Python changes needed)

| User says                      | Action                              |
|-------------------------------|-------------------------------------|
| "Jarvis standby"               | → Offline Mode                      |
| "I'm going out"                | → Offline Mode                      |
| "I'll be back in 10 minutes"  | → Offline Mode + 10min countdown    |
| "I'm back" / "Wake up Jarvis" | → Online Mode + Spotify wake-up     |
| "Open workspace"               | → VS Code + Claude + Chrome tabs    |
| "Show weather"                 | → Weather widget (needs WS data)    |
| "Show map of Delhi"            | → Maps widget                       |
| "Open camera"                  | → Camera widget (webcam)            |
| "Clipboard"                    | → Clipboard widget                  |

---

## Personality Mode (data-personality-mode on body)

Set from Python via:
```json
{ "type": "user_profile", "data": { "mode": "professional|friendly|admin" } }
```

- **friendly** → green badge, Hinglish mode
- **professional** → cyan badge, English only
- **admin** → purple badge, technical mode
