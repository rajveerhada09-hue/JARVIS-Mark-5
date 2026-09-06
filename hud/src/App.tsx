import { useEffect, useState, useCallback } from 'react';
import { backendService } from './services/BackendService';
import type { AIState, SystemStats, ConversationMessage, WSMessage } from './types';
import { deriveSystemStatus, simulateStats } from './hud/core/constants';

function App() {
  const [aiState, setAiState] = useState<AIState>('idle');
  const [systemStats, setSystemStats] = useState<SystemStats>(simulateStats());
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const [currentProvider] = useState('unknown');
  const [offlineMode] = useState(false);
  const [listening, setListening] = useState(false);

  useEffect(() => {
    backendService.connect();

    const unsub = backendService.subscribe((msg: WSMessage) => {
      const parsed = backendService.parseMessage(msg);
      if (!parsed) return;

      if (parsed.aiState) {
        setAiState(parsed.aiState);
        setListening(parsed.aiState === 'listening');
      }
      if (parsed.stats) {
        setSystemStats(parsed.stats);
      }
      if (parsed.message) {
        setMessages(prev => [...prev.slice(-49), parsed.message!]);
      }
      if (parsed.notification) {
        console.log('[HUD] Notification:', parsed.notification);
      }
    });

    backendService.subscribe(() => {
      setConnected(backendService.connected);
    });

    // Request initial status
    backendService.send('get_status', {});

    return () => {
      unsub();
      backendService.disconnect();
    };
  }, []);

  const sendCommand = useCallback((type: string, data: unknown = {}) => {
    backendService.send(type, data);
  }, []);

  const handleListen = () => {
    sendCommand('listen', {});
    setListening(true);
  };

  const handleStopListen = () => {
    sendCommand('stop_listen', {});
    setListening(false);
  };

  const handleClearMessages = () => {
    setMessages([]);
  };

  const status = deriveSystemStatus(aiState, 'online', false, false);

  return (
    <div className="hud-grid min-h-screen w-full flex flex-col">
      {/* Top Status Bar */}
      <header className="glass-panel border-b border-cyan-glow/20 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="hud-text-glow text-xl font-mono tracking-wider text-cyan">
            JARVIS MARK 5
          </div>
          <div className="flex items-center gap-2 px-3 py-1 glass-panel border border-cyan-glow/30 rounded">
            <span className={`hud-label text-xs ${connected ? 'text-green-400' : 'text-red-400'}`}>
              {connected ? 'ONLINE' : 'OFFLINE'}
            </span>
            <span className="w-2 h-2 rounded-full transition-colors"
              style={{ backgroundColor: connected ? '#00ff88' : '#ff4444' }} />
          </div>
        </div>

        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <span className="hud-label text-xs text-cyan-dim">STT</span>
            <span className="font-mono text-cyan">{currentProvider.toUpperCase()}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="hud-label text-xs text-cyan-dim">STATE</span>
            <span className={`font-mono hud-text-glow ${listening ? 'text-amber' : 'text-cyan'}`}>
              {status}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1 glass-panel px-2 py-1 border border-cyan-glow/20 rounded">
            <span className="hud-label text-xs">CPU</span>
            <span className="font-mono text-cyan">{systemStats.cpu?.toFixed(0) || 0}%</span>
          </div>
          <div className="flex items-center gap-1 glass-panel px-2 py-1 border border-cyan-glow/20 rounded">
            <span className="hud-label text-xs">RAM</span>
            <span className="font-mono text-cyan">{systemStats.ram?.toFixed(0) || 0}%</span>
          </div>
          {systemStats.battery && (
            <div className="flex items-center gap-1 glass-panel px-2 py-1 border border-cyan-glow/20 rounded">
              <span className="hud-label text-xs">BAT</span>
              <span className="font-mono text-cyan">{systemStats.battery}%</span>
            </div>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex overflow-hidden p-4 gap-4">
        {/* Left Panel - Conversation & Controls */}
        <div className="w-96 flex flex-col gap-4 glass-panel border border-cyan-glow/20 rounded-xl overflow-hidden">
          {/* Conversation History */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            <div className="flex items-center justify-between mb-4">
              <span className="hud-label text-cyan-dim">CONVERSATION</span>
              <button
                onClick={handleClearMessages}
                className="hud-label text-xs text-cyan-dim hover:text-cyan transition-colors px-2 py-1"
              >
                CLEAR
              </button>
            </div>

            {messages.length === 0 ? (
              <div className="text-center text-cyan-dim/50 py-8">
                <p className="hud-label mb-2">NO MESSAGES</p>
                <p className="text-sm">Say "Jarvis" to begin</p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={`flex flex-col gap-1 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <span className={`hud-label text-xs ${msg.role === 'user' ? 'text-amber' : 'text-cyan'}`}>
                    {msg.role.toUpperCase()}
                  </span>
                  <div className={`glass-panel p-3 rounded-lg max-w-full ${msg.role === 'user' ? 'bg-amber-glow/10 border-amber-glow/30' : 'border-cyan-glow/20'}`}>
                    <p className="text-sm whitespace-pre-wrap break-words">{msg.text}</p>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Control Buttons */}
          <div className="p-4 border-t border-cyan-glow/20 flex flex-col gap-3">
            <button
              onClick={handleListen}
              disabled={listening}
              className={`w-full py-3 rounded-lg font-mono hud-text-glow transition-all ${
                listening
                  ? 'bg-amber-glow/20 border-amber-glow/50 text-amber cursor-not-allowed'
                  : 'bg-cyan-glow/10 border-cyan-glow/30 text-cyan hover:bg-cyan-glow/20'
              }`}
            >
              {listening ? 'LISTENING...' : 'ACTIVATE LISTENING'}
            </button>

            <button
              onClick={handleStopListen}
              disabled={!listening}
              className="w-full py-3 rounded-lg font-mono hud-text-glow transition-all bg-red-900/20 border-red-500/30 text-red-400 hover:bg-red-900/30 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              STOP LISTENING
            </button>

            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => sendCommand('get_status', {})}
                className="py-2 rounded-lg font-mono text-xs hud-text-glow transition-all bg-cyan-glow/10 border-cyan-glow/30 text-cyan hover:bg-cyan-glow/20"
              >
                REFRESH STATUS
              </button>
              <button
                onClick={() => sendCommand('toggle_offline', {})}
                className={`py-2 rounded-lg font-mono text-xs hud-text-glow transition-all ${
                  offlineMode
                    ? 'bg-amber-glow/20 border-amber-glow/50 text-amber'
                    : 'bg-cyan-glow/10 border-cyan-glow/30 text-cyan hover:bg-cyan-glow/20'
                }`}
              >
                {offlineMode ? 'ONLINE MODE' : 'OFFLINE MODE'}
              </button>
            </div>
          </div>
        </div>

        {/* Center Panel - Visualizer / Status Display */}
        <div className="flex-1 flex flex-col gap-4 min-w-0">
          {/* AI State Visualizer */}
          <div className="flex-1 glass-panel border border-cyan-glow/20 rounded-xl flex items-center justify-center relative overflow-hidden">
            <div className="relative z-10 text-center">
              <div
                className={`w-32 h-32 mx-auto mb-6 rounded-full transition-all duration-500 ${
                  listening
                    ? 'bg-amber-glow/30 border-4 border-amber animate-pulse'
                    : aiState === 'thinking'
                    ? 'bg-cyan-glow/20 border-2 border-cyan animate-pulse'
                    : aiState === 'speaking'
                    ? 'bg-cyan-glow/30 border-2 border-cyan'
                    : 'bg-cyan-glow/10 border border-cyan-glow/30'
                }`}
              />
              <div className="font-mono text-2xl hud-text-glow text-cyan mb-2">{status}</div>
              <div className="hud-label text-cyan-dim tracking-wider">{aiState.toUpperCase()}</div>
            </div>

            {/* Background grid animation */}
            <div className="absolute inset-0 hud-grid opacity-20" />
          </div>

          {/* System Metrics */}
          <div className="glass-panel border border-cyan-glow/20 rounded-xl p-4">
            <div className="hud-label text-cyan-dim mb-4">SYSTEM METRICS</div>
            <div className="grid grid-cols-4 gap-4 text-center">
              <MetricCard label="CPU" value={`${systemStats.cpu?.toFixed(0) || 0}%`} unit="cores: {systemStats.cpu_cores || '?'}" />
              <MetricCard label="RAM" value={`${systemStats.ram?.toFixed(0) || 0}%`} unit={`${(systemStats.ramUsed || 0).toFixed(1)}/{systemStats.ramTotal || 0} GB`} />
              <MetricCard label="GPU" value={`${systemStats.gpu?.toFixed(0) || 0}%`} unit={systemStats.gpuName || 'N/A'} />
              <MetricCard label="DISK" value={`${systemStats.disk?.toFixed(0) || 0}%`} unit="used" />
            </div>
            <div className="grid grid-cols-4 gap-4 text-center mt-4 pt-4 border-t border-cyan-glow/20">
              <MetricCard label="NET ↑" value={`${(systemStats.netUp || 0).toFixed(0)} KB/s`} />
              <MetricCard label="NET ↓" value={`${(systemStats.netDown || 0).toFixed(0)} KB/s`} />
              <MetricCard label="TEMP" value={`${systemStats.temperature || 0}°C`} />
              <MetricCard label="PROC" value={`${systemStats.processes || 0}`} />
            </div>
          </div>
        </div>

        {/* Right Panel - Provider Status & Settings */}
        <div className="w-80 flex flex-col gap-4 glass-panel border border-cyan-glow/20 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-cyan-glow/20">
            <span className="hud-label text-cyan-dim">PROVIDER STATUS</span>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            <ProviderStatus name="Deepgram (Nova-3)" status={currentProvider === 'deepgram' ? 'active' : 'available'} requiresNetwork />
            <ProviderStatus name="OpenAI Whisper" status={currentProvider === 'openai' ? 'active' : 'available'} requiresNetwork />
            <ProviderStatus name="Faster-Whisper (Local)" status={currentProvider === 'faster-whisper' ? 'active' : 'fallback'} />
          </div>

          <div className="p-4 border-t border-cyan-glow/20 space-y-3">
            <div className="hud-label text-cyan-dim">QUICK ACTIONS</div>
            <button
              onClick={() => sendCommand('speak', { text: 'Systems nominal, Sir.' })}
              className="w-full py-2 rounded-lg font-mono text-xs hud-text-glow transition-all bg-cyan-glow/10 border-cyan-glow/30 text-cyan hover:bg-cyan-glow/20"
            >
              TEST TTS
            </button>
            <button
              onClick={() => sendCommand('system_stats', {})}
              className="w-full py-2 rounded-lg font-mono text-xs hud-text-glow transition-all bg-cyan-glow/10 border-cyan-glow/30 text-cyan hover:bg-cyan-glow/20"
            >
              REQUEST STATS
            </button>
            <button
              onClick={() => sendCommand('test_stt', {})}
              className="w-full py-2 rounded-lg font-mono text-xs hud-text-glow transition-all bg-cyan-glow/10 border-cyan-glow/30 text-cyan hover:bg-cyan-glow/20"
            >
              TEST STT
            </button>
          </div>
        </div>
      </main>

      {/* Bottom Status Bar */}
      <footer className="glass-panel border-t border-cyan-glow/20 px-4 py-2 flex items-center justify-between text-xs">
        <div className="flex items-center gap-4 hud-label text-cyan-dim">
          <span>JARVIS MARK 5</span>
          <span>|</span>
          <span>STT: {currentProvider.toUpperCase()}</span>
          <span>|</span>
          <span>LLM: GEMINI</span>
          <span>|</span>
          <span>{offlineMode ? 'OFFLINE' : 'ONLINE'}</span>
        </div>
        <div className="hud-label text-cyan-dim">
          {new Date().toLocaleTimeString()}
        </div>
      </footer>
    </div>
  );
}

function MetricCard({ label, value, unit }: { label: string; value: string; unit?: string }) {
  return (
    <div className="glass-panel p-3 rounded-lg border border-cyan-glow/10">
      <div className="hud-label text-xs text-cyan-dim mb-1">{label}</div>
      <div className="font-mono text-lg hud-text-glow text-cyan">{value}</div>
      {unit && <div className="hud-label text-xs text-cyan-dim/70">{unit}</div>}
    </div>
  );
}

function ProviderStatus({ name, status, requiresNetwork = false }: {
  name: string;
  status: 'active' | 'available' | 'fallback';
  requiresNetwork?: boolean;
}) {
  const statusColors = {
    active: 'text-green-400 border-green-400/30 bg-green-400/10',
    available: 'text-cyan border-cyan-glow/30 bg-cyan-glow/10',
    fallback: 'text-amber border-amber-glow/30 bg-amber-glow/10',
  };

  return (
    <div className={`glass-panel p-3 rounded-lg border ${statusColors[status]}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="font-mono text-sm">{name}</span>
        <span className={`hud-label text-xs ${statusColors[status].split(' ')[0]}`}>
          {status.toUpperCase()}
        </span>
      </div>
      {requiresNetwork && (
        <span className="hud-label text-xs text-cyan-dim/70">REQUIRES NETWORK</span>
      )}
    </div>
  );
}

export default App;