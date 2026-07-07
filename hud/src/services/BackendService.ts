import type { WSMessage, SystemStats, AIState, ConversationMessage } from '@/types';

export type BackendEventHandler = (msg: WSMessage) => void;

/**
 * Service interface for Python Kernel integration.
 * Connects via WebSocket bridge (hud/websocket/server.js).
 */
export class BackendService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectMs: number;
  private handlers = new Set<BackendEventHandler>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private _connected = false;

  constructor(url = 'ws://localhost:8765', reconnectMs = 3000) {
    this.url = url;
    this.reconnectMs = reconnectMs;
  }

  get connected(): boolean {
    return this._connected;
  }

  connect(): void {
    if (this.ws) {
      try {
        this.ws.close();
      } catch {
        /* ignore */
      }
    }

    try {
      this.ws = new WebSocket(this.url);
    } catch {
      this.scheduleReconnect();
      return;
    }

    this.ws.addEventListener('open', () => {
      this._connected = true;
      this.emit({ type: 'connection', data: { status: 'connected' } });
    });

    this.ws.addEventListener('close', () => {
      this._connected = false;
      this.emit({ type: 'connection', data: { status: 'disconnected' } });
      this.scheduleReconnect();
    });

    this.ws.addEventListener('error', () => this.ws?.close());

    this.ws.addEventListener('message', (evt) => {
      try {
        const msg = JSON.parse(evt.data as string) as WSMessage;
        this.emit(msg);
      } catch {
        /* malformed */
      }
    });
  }

  disconnect(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
    this._connected = false;
  }

  subscribe(handler: BackendEventHandler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  send(type: string, data: unknown = {}): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data }));
    }
  }

  /** Route common kernel message types */
  parseMessage(msg: WSMessage): {
    aiState?: AIState;
    stats?: SystemStats;
    message?: ConversationMessage;
    notification?: string;
    mode?: string;
    action?: string;
  } | null {
    const { type, data } = msg;
    const d = data as Record<string, unknown>;

    switch (type) {
      case 'state':
        return { aiState: d.state as AIState };
      case 'stats':
        return { stats: d as unknown as SystemStats };
      case 'message':
        return {
          message: {
            role: d.role as ConversationMessage['role'],
            text: String(d.text ?? ''),
            timestamp: Date.now(),
          },
        };
      case 'notification':
        return { notification: String(d.text ?? '') };
      case 'command': {
        const action = String(d.action ?? '');
        if (action === 'mode') return { mode: String(d.mode ?? ''), action };
        return { action };
      }
      default:
        return null;
    }
  }

  private emit(msg: WSMessage): void {
    this.handlers.forEach((h) => h(msg));
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => this.connect(), this.reconnectMs);
  }
}

export const backendService = new BackendService();
