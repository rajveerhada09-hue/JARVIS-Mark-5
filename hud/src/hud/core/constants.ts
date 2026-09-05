import type {
  AIState,
  FocusMode,
  HUDMode,
  LayoutPreset,
  SystemStats,
  SystemStatus,
  ThemeConfig,
  WidgetId,
} from '@/types';

export const AI_TO_SYSTEM_STATUS: Record<AIState, SystemStatus> = {
  idle: 'ONLINE',
  listening: 'LISTENING',
  thinking: 'THINKING',
  speaking: 'VOICE_ACTIVE',
  executing: 'EXECUTING',
  searching: 'PROCESSING',
  offline: 'OFFLINE',
};

export const DEFAULT_THEME: ThemeConfig = {
  accent: '#00e5ff',
  glowIntensity: 1,
  particleDensity: 80,
  gridOpacity: 0.03,
  animationSpeed: 1,
};

export const FOCUS_PRESETS: Record<FocusMode, LayoutPreset> = {
  focus: {
    mode: 'focus',
    visibleWidgets: [],
    dockVisible: false,
    theme: { particleDensity: 40, glowIntensity: 0.8 },
  },
  homework: {
    mode: 'homework',
    visibleWidgets: ['notes', 'browser'],
    dockVisible: true,
    theme: { accent: '#64b5f6', particleDensity: 50 },
  },
  developer: {
    mode: 'developer',
    visibleWidgets: ['terminal', 'browser', 'system'],
    dockVisible: true,
    theme: { accent: '#00e676', particleDensity: 60 },
  },
  gaming: {
    mode: 'gaming',
    visibleWidgets: ['system', 'media'],
    dockVisible: true,
    theme: { accent: '#ff4081', glowIntensity: 1.2, animationSpeed: 1.3 },
  },
  media: {
    mode: 'media',
    visibleWidgets: ['media', 'spotify'],
    dockVisible: true,
    theme: { accent: '#1db954', particleDensity: 70 },
  },
  research: {
    mode: 'research',
    visibleWidgets: ['browser', 'notes', 'map'],
    dockVisible: true,
    theme: { accent: '#7c4dff' },
  },
  presentation: {
    mode: 'presentation',
    visibleWidgets: ['clock'],
    dockVisible: false,
    theme: { particleDensity: 30, gridOpacity: 0.02 },
  },
  admin: {
    mode: 'admin',
    visibleWidgets: ['system', 'terminal', 'memory'],
    dockVisible: true,
    theme: { accent: '#ffab40', glowIntensity: 0.9 },
  },
};

export const HUD_MODE_STATUS: Record<HUDMode, SystemStatus> = {
  online: 'ONLINE',
  standby: 'STANDBY',
  processor: 'GPU_INFERENCE',
};

export const WIDGET_REGISTRY: Record<
  WidgetId,
  { title: string; defaultWidth: number; defaultHeight: number }
> = {
  browser: { title: 'Browser', defaultWidth: 900, defaultHeight: 560 },
  media: { title: 'Media Player', defaultWidth: 720, defaultHeight: 420 },
  notes: { title: 'Notes', defaultWidth: 420, defaultHeight: 480 },
  map: { title: 'Maps', defaultWidth: 680, defaultHeight: 520 },
  weather: { title: 'Weather', defaultWidth: 320, defaultHeight: 280 },
  terminal: { title: 'Terminal', defaultWidth: 640, defaultHeight: 400 },
  clock: { title: 'Clock', defaultWidth: 280, defaultHeight: 160 },
  system: { title: 'System Monitor', defaultWidth: 380, defaultHeight: 340 },
  ai: { title: 'AI Assistant', defaultWidth: 480, defaultHeight: 520 },
  camera: { title: 'Camera', defaultWidth: 480, defaultHeight: 360 },
  vision: { title: 'Vision', defaultWidth: 520, defaultHeight: 400 },
  memory: { title: 'Memory', defaultWidth: 360, defaultHeight: 300 },
  spotify: { title: 'Spotify', defaultWidth: 340, defaultHeight: 200 },
};

export function deriveSystemStatus(
  aiState: AIState,
  hudMode: HUDMode,
  booting: boolean,
  error: boolean,
): SystemStatus {
  if (booting) return 'BOOTING';
  if (error) return 'ERROR';
  if (hudMode === 'standby') return 'STANDBY';
  if (hudMode === 'processor') return 'GPU_INFERENCE';
  if (aiState === 'offline') return 'OFFLINE';
  return AI_TO_SYSTEM_STATUS[aiState] ?? 'ONLINE';
}

export function pad(n: number): string {
  return String(n).padStart(2, '0');
}

export function escapeHtml(s: string): string {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

export function formatBytes(b: number): string {
  if (b < 1024) return `${b.toFixed(0)} B`;
  if (b < 1048576) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / 1048576).toFixed(1)} MB`;
}

export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

export function createId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

/** Simulated stats until backend connects */
export function simulateStats(prev?: SystemStats): SystemStats {
  const cpu = clamp((prev?.cpu ?? 14) + (Math.random() - 0.48) * 6, 5, 95);
  const ram = clamp((prev?.ram ?? 42) + (Math.random() - 0.49) * 2, 20, 90);
  return {
    cpu,
    cpu_cores: 8,
    ram,
    ramUsed: (ram / 100) * 16,
    ramTotal: 16,
    gpu: clamp((prev?.gpu ?? 22) + (Math.random() - 0.5) * 4, 0, 100),
    gpuName: 'RTX Neural Core',
    disk: 55,
    netUp: Math.random() * 50000,
    netDown: Math.random() * 200000,
    internet: true,
    battery: 87,
    temperature: 48 + Math.floor(Math.random() * 8),
    processes: 140 + Math.floor(Math.random() * 40),
  } as SystemStats & { cpu_cores?: number };
}
