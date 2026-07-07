/** AI core visual states */
export type AIState =
  | 'idle'
  | 'listening'
  | 'thinking'
  | 'speaking'
  | 'executing'
  | 'searching'
  | 'offline';

/** HUD display modes */
export type HUDMode =
  | 'online'
  | 'standby'
  | 'processor';

/** System status shown in status bar */
export type SystemStatus =
  | 'ONLINE'
  | 'LISTENING'
  | 'THINKING'
  | 'PROCESSING'
  | 'EXECUTING'
  | 'VOICE_ACTIVE'
  | 'GPU_INFERENCE'
  | 'LOCAL_MODEL'
  | 'STANDBY'
  | 'OFFLINE'
  | 'ERROR'
  | 'BOOTING';

/** Focus / workspace modes */
export type FocusMode =
  | 'focus'
  | 'homework'
  | 'developer'
  | 'gaming'
  | 'media'
  | 'research'
  | 'presentation'
  | 'admin';

export type WidgetId =
  | 'browser'
  | 'media'
  | 'notes'
  | 'map'
  | 'weather'
  | 'terminal'
  | 'clock'
  | 'system'
  | 'ai'
  | 'camera'
  | 'vision'
  | 'memory'
  | 'spotify';

export type DockItemId =
  | 'browser'
  | 'terminal'
  | 'spotify'
  | 'maps'
  | 'notes'
  | 'weather'
  | 'camera'
  | 'vision'
  | 'memory'
  | 'ai';

export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface WindowState {
  id: string;
  widgetId: WidgetId;
  title: string;
  rect: Rect;
  zIndex: number;
  minimized: boolean;
  maximized: boolean;
  pinned: boolean;
  docked: boolean;
}

export interface WidgetDefinition {
  id: WidgetId;
  title: string;
  defaultSize: { width: number; height: number };
  minSize?: { width: number; height: number };
  refreshInterval?: number;
}

export interface SystemStats {
  cpu?: number;
  ram?: number;
  ramUsed?: number;
  ramTotal?: number;
  gpu?: number;
  gpuName?: string;
  disk?: number;
  netUp?: number;
  netDown?: number;
  internet?: boolean;
  battery?: number;
  temperature?: number;
  processes?: number;
}

export interface WSMessage<T = unknown> {
  type: string;
  data: T;
}

export interface ConversationMessage {
  role: 'user' | 'assistant' | 'system';
  text: string;
  timestamp: number;
}

export interface NotificationItem {
  id: string;
  text: string;
  timestamp: number;
  priority?: 'low' | 'normal' | 'high';
}

export interface ThemeConfig {
  accent: string;
  glowIntensity: number;
  particleDensity: number;
  gridOpacity: number;
  animationSpeed: number;
}

export interface LayoutPreset {
  mode: FocusMode;
  visibleWidgets: WidgetId[];
  dockVisible: boolean;
  theme: Partial<ThemeConfig>;
}

export interface ElectronAPI {
  openWorkspace?: () => void;
  playSpotify?: (trackId: string) => void;
  openExternal?: (url: string) => void;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}
