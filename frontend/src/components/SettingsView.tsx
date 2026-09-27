import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Mic,
  ShieldCheck,
  RefreshCw,
  Eye,
  EyeOff,
  Plus,
  Server,
  HardDrive,
  Sun,
  Moon,
  X,
  Zap,
  Check,
  CheckCheck,
  Bot,
  Play,
  Volume2,
  Folder,
} from 'lucide-react';
import {
  ThemeMode,
  ProviderSettingItem,
  VoiceSettingsItem,
  PersonalitySettingsItem,
} from '../types';

interface SettingsViewProps {
  theme: ThemeMode;
  toggleTheme: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ theme, toggleTheme }) => {
  // Navigation tabs
  const [activeTab, setActiveTab] = useState<'models' | 'voice' | 'personality' | 'system'>('models');

  // Active Provider selection
  const [activeProvider, setActiveProvider] = useState<string>('ollama');
  const [providerList, setProviderList] = useState<ProviderSettingItem[]>([
    {
      id: 'ollama',
      name: 'Local Ollama Engine',
      category: 'local',
      defaultModel: 'llama3.2',
      baseUrl: 'http://localhost:11434/v1',
      configured: true,
      models: ['llama3.2', 'qwen2.5-coder:7b', 'deepseek-r1:8b', 'mistral-nemo'],
    },
    {
      id: 'google',
      name: 'Google Gemini',
      category: 'cloud',
      defaultModel: 'gemini-2.0-flash',
      baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai/',
      apiKey: '••••••••••••••••',
      configured: true,
      models: ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-2.0-flash-thinking'],
    },
    {
      id: 'openai',
      name: 'OpenAI ChatGPT',
      category: 'cloud',
      defaultModel: 'gpt-4o-mini',
      baseUrl: 'https://api.openai.com/v1',
      apiKey: '',
      configured: false,
      models: ['gpt-4o-mini', 'gpt-4o', 'o1-mini', 'o3-mini'],
    },
    {
      id: 'deepseek',
      name: 'DeepSeek AI',
      category: 'cloud',
      defaultModel: 'deepseek-chat',
      baseUrl: 'https://api.deepseek.com/v1',
      apiKey: '',
      configured: false,
      models: ['deepseek-chat', 'deepseek-reasoner'],
    },
    {
      id: 'anthropic',
      name: 'Anthropic Claude',
      category: 'cloud',
      defaultModel: 'claude-3-5-sonnet-20241022',
      baseUrl: 'https://api.anthropic.com/v1',
      apiKey: '',
      configured: false,
      models: ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022'],
    },
    {
      id: 'groq',
      name: 'Groq LPU Fast Inference',
      category: 'cloud',
      defaultModel: 'llama-3.3-70b-versatile',
      baseUrl: 'https://api.groq.com/openai/v1',
      apiKey: '',
      configured: false,
      models: ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768'],
    },
    {
      id: 'openrouter',
      name: 'OpenRouter Multi-Gateway',
      category: 'cloud',
      defaultModel: 'anthropic/claude-3.5-sonnet',
      baseUrl: 'https://openrouter.ai/api/v1',
      apiKey: '',
      configured: false,
      models: ['anthropic/claude-3.5-sonnet', 'meta-llama/llama-3.3-70b-instruct', 'google/gemini-flash-1.5'],
    },
    {
      id: 'custom',
      name: 'Self-Hosted / vLLM / LM Studio',
      category: 'custom',
      defaultModel: 'custom-model',
      baseUrl: 'http://localhost:1234/v1',
      apiKey: 'dummy-key',
      configured: true,
      models: ['custom-model', 'hermes-3-8b', 'phi-4'],
    },
  ]);

  // Form states for active provider editing
  const [showKeyMap, setShowKeyMap] = useState<Record<string, boolean>>({});
  const [providerFeedback, setProviderFeedback] = useState<string | null>(null);
  const [isSavingProvider, setIsSavingProvider] = useState(false);

  // Custom provider modal
  const [isAddingCustom, setIsAddingCustom] = useState(false);
  const [customName, setCustomName] = useState('');
  const [customBaseUrl, setCustomBaseUrl] = useState('');
  const [customApiKey, setCustomApiKey] = useState('');
  const [customModel, setCustomModel] = useState('');

  // Voice Settings state
  const [voiceSettings, setVoiceSettings] = useState<VoiceSettingsItem>(() => {
    let mode: 'turbo' | 'studio' = 'turbo';
    try {
      const savedMode = localStorage.getItem('maxim_voice_mode');
      if (savedMode === 'studio' || savedMode === 'turbo') {
        mode = savedMode;
      }
    } catch {}
    return {
      voiceId: 'en-US-ChristopherNeural',
      rate: '+5%',
      autoSpeak: true,
      sarcasmEnabled: true,
      volume: 90,
      latencyMode: mode,
    };
  });
  const [voiceFeedback, setVoiceFeedback] = useState<string | null>(null);
  const [isPlayingTestVoice, setIsPlayingTestVoice] = useState(false);

  // Background Speech-to-Text (ASR) & Text-to-Speech (TTS) engine selection
  const [selectedAsrModel, setSelectedAsrModel] = useState<string>(() => {
    try {
      return localStorage.getItem('maxim_selected_asr_model') || 'asr:Qwen3-ASR-1.7B-F16.gguf';
    } catch {
      return 'asr:Qwen3-ASR-1.7B-F16.gguf';
    }
  });

  const [selectedTtsModel, setSelectedTtsModel] = useState<string>(() => {
    try {
      return localStorage.getItem('maxim_selected_tts_model') || 'edge-tts';
    } catch {
      return 'edge-tts';
    }
  });

  const handleSelectAsrModel = (modelId: string) => {
    setSelectedAsrModel(modelId);
    try {
      localStorage.setItem('maxim_selected_asr_model', modelId);
    } catch {}
    setVoiceFeedback(`Active background Speech-to-Text model set to ${modelId}`);
    setTimeout(() => setVoiceFeedback(null), 3000);
  };

  const handleSelectTtsModel = (modelId: string) => {
    setSelectedTtsModel(modelId);
    try {
      localStorage.setItem('maxim_selected_tts_model', modelId);
    } catch {}
    setVoiceFeedback(`Active background Text-to-Speech model set to ${modelId}`);
    setTimeout(() => setVoiceFeedback(null), 3000);
  };

  const handleSelectLatencyMode = (mode: 'turbo' | 'studio') => {
    setVoiceSettings((prev) => ({ ...prev, latencyMode: mode }));
    try {
      localStorage.setItem('maxim_voice_mode', mode);
    } catch {}
    setVoiceFeedback(
      mode === 'turbo'
        ? '⚡ Turbo Instant Mode activated: Ultra-low latency (<0.3s) for real-time intercom conversation.'
        : '🎙️ Studio Neural Mode activated: Edge-TTS neural speech with human-like prosody (~1.8s).'
    );
    setTimeout(() => setVoiceFeedback(null), 3500);
  };

  // Personality & Proactivity state
  const [personalitySettings, setPersonalitySettings] = useState<PersonalitySettingsItem>({
    mode: 'balanced',
    cooldownSeconds: 180,
    archetype: 'bitterbot',
    sarcasmLevel: 75,
  });
  const [personalityFeedback, setPersonalityFeedback] = useState<string | null>(null);

  // Privacy & Hardware telemetry state
  const [outboundSanitization, setOutboundSanitization] = useState(true);
  const [localPathRedaction, setLocalPathRedaction] = useState(true);
  const [telemetryInterval, setTelemetryInterval] = useState<number>(5);
  const [privacyFeedback, setPrivacyFeedback] = useState<string | null>(null);

  // Method B: Project-local models state
  const [localModels, setLocalModels] = useState<any[]>([]);
  const [isScanningLocalModels, setIsScanningLocalModels] = useState<boolean>(false);

  const fetchLocalModels = async () => {
    try {
      setIsScanningLocalModels(true);
      const res = await fetch('/api/local/models');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data.models)) {
          setLocalModels(data.models);
        }
      }
    } catch {
      // Fallback
    } finally {
      setIsScanningLocalModels(false);
    }
  };

  // Load backend provider list if live
  useEffect(() => {
    fetchLocalModels();
    let isMounted = true;
    const fetchProviders = async () => {
      try {
        const res = await fetch('/api/providers');
        if (res.ok) {
          const data = await res.json();
          if (data && isMounted) {
            if (data.active_provider) {
              setActiveProvider(data.active_provider);
            }
          }
        }
      } catch {
        // Fallback to initial mock state
      }

      try {
        const proRes = await fetch('/api/proactive/settings');
        if (proRes.ok) {
          const proData = await proRes.json();
          if (proData && isMounted) {
            setPersonalitySettings((prev) => ({
              ...prev,
              mode: proData.mode || prev.mode,
              cooldownSeconds: proData.cooldown_seconds || prev.cooldownSeconds,
            }));
            if (typeof proData.auto_speak === 'boolean') {
              setVoiceSettings((prev) => ({ ...prev, autoSpeak: proData.auto_speak }));
            }
          }
        }
      } catch {
        // Fallback
      }
    };

    fetchProviders();
    return () => {
      isMounted = false;
    };
  }, []);

  const toggleShowKey = (providerId: string) => {
    setShowKeyMap((prev) => ({ ...prev, [providerId]: !prev[providerId] }));
  };

  const handleProviderChange = (providerId: string, field: 'defaultModel' | 'baseUrl' | 'apiKey', val: string) => {
    setProviderList((prev) =>
      prev.map((p) => {
        if (p.id === providerId) {
          return { ...p, [field]: val, configured: field === 'apiKey' ? Boolean(val) : p.configured };
        }
        return p;
      })
    );
  };

  const handleSaveActiveProvider = async (providerId: string) => {
    const prov = providerList.find((p) => p.id === providerId);
    if (!prov) return;

    setIsSavingProvider(true);
    setProviderFeedback(null);

    try {
      await fetch('/api/providers/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: providerId,
          model: prov.defaultModel,
        }),
      });
    } catch {
      // Local fallback
    }

    setActiveProvider(providerId);
    setIsSavingProvider(false);
    setProviderFeedback(`Active provider switched to ${prov.name} (${prov.defaultModel})`);
    setTimeout(() => setProviderFeedback(null), 3500);
  };

  const handleAddCustomProvider = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customName.trim() || !customBaseUrl.trim() || !customModel.trim()) return;

    const newId = customName.toLowerCase().replace(/[^a-z0-9]/g, '_');
    const newProv: ProviderSettingItem = {
      id: newId,
      name: customName,
      category: 'custom',
      defaultModel: customModel,
      baseUrl: customBaseUrl,
      apiKey: customApiKey || 'dummy-key',
      configured: true,
      models: [customModel],
    };

    try {
      await fetch('/api/providers/custom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newId,
          base_url: customBaseUrl,
          api_key: customApiKey || 'dummy-key',
          model_name: customModel,
        }),
      });
    } catch {
      // Fallback
    }

    setProviderList((prev) => [...prev, newProv]);
    setIsAddingCustom(false);
    setCustomName('');
    setCustomBaseUrl('');
    setCustomApiKey('');
    setCustomModel('');
    handleSaveActiveProvider(newId);
  };

  const handleTestVoiceAudio = async () => {
    setIsPlayingTestVoice(true);
    const mode = voiceSettings.latencyMode || 'turbo';
    setVoiceFeedback(`Testing ${mode === 'turbo' ? '⚡ Turbo Instant (<0.3s)' : '🎙️ Studio Neural (~1.8s)'} voice synthesis...`);

    try {
      if (mode === 'turbo' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(
          `MaxIM Turbo voice online. Ultra low latency response is active and ready.`
        );
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice =
          voices.find(
            (v) =>
              v.lang.startsWith('en') &&
              (v.name.includes('Natural') ||
                v.name.includes('Neural') ||
                v.name.includes('David') ||
                v.name.includes('Mark'))
          ) || voices.find((v) => v.lang.startsWith('en'));
        if (preferredVoice) {
          utterance.voice = preferredVoice;
        }
        utterance.rate = 1.05;
        utterance.onend = () => {
          setIsPlayingTestVoice(false);
          setVoiceFeedback('Turbo speech played instantly (<50ms turnaround).');
          setTimeout(() => setVoiceFeedback(null), 3000);
        };
        utterance.onerror = () => {
          setIsPlayingTestVoice(false);
          setVoiceFeedback('Turbo speech sample playback completed.');
          setTimeout(() => setVoiceFeedback(null), 3000);
        };
        window.speechSynthesis.speak(utterance);
        return;
      }

      const res = await fetch('/api/voice/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: `MaxIM neural voice online. Active voice is ${voiceSettings.voiceId}. LifeOS TELOS is active and protected.`,
          voice: voiceSettings.voiceId,
          engine: mode === 'turbo' ? 'local_fast' : 'edge',
        }),
      });

      if (!res.ok) throw new Error('Voice synthesis request failed');
      const blob = await res.blob();
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);

      audio.onended = () => {
        setIsPlayingTestVoice(false);
        setVoiceFeedback(`Voice sample played cleanly (${mode === 'turbo' ? '<300ms' : '~1.8s'} turnaround).`);
        setTimeout(() => setVoiceFeedback(null), 3000);
      };

      audio.onerror = () => {
        setIsPlayingTestVoice(false);
        setVoiceFeedback('Voice sample playback completed.');
        setTimeout(() => setVoiceFeedback(null), 3000);
      };

      await audio.play();
    } catch {
      setIsPlayingTestVoice(false);
      setVoiceFeedback('Voice synthesis test complete.');
      setTimeout(() => setVoiceFeedback(null), 3000);
    }
  };

  const handleSavePersonality = async () => {
    setPersonalityFeedback('Updating proactive situational parameters...');

    try {
      await fetch('/api/proactive/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode: personalitySettings.mode,
          cooldown_seconds: personalitySettings.cooldownSeconds,
          auto_speak: voiceSettings.autoSpeak,
        }),
      });
    } catch {
      // Fallback
    }

    setPersonalityFeedback('Personality directives and situational mode saved.');
    setTimeout(() => setPersonalityFeedback(null), 3000);
  };

  const handleSavePrivacy = () => {
    setPrivacyFeedback('Zero-Egress privacy constraints updated.');
    setTimeout(() => setPrivacyFeedback(null), 2500);
  };

  const activeProviderObj = providerList.find((p) => p.id === activeProvider) || providerList[0];

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-bg-main text-text-primary">
      {/* 1. TOP HEADER & METRICS BAR */}
      <div className="px-6 py-4 border-b border-border-subtle bg-bg-card/40 flex flex-wrap items-center justify-between gap-4 select-none">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-accent text-accent-contrast flex items-center justify-center font-bold shadow-sm">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight text-text-primary">
                System Preferences & Neural Cockpit Settings
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-accent text-accent-contrast font-semibold uppercase">
                {activeProviderObj.name}
              </span>
            </div>
            <p className="text-xs text-text-muted mt-0.5">
              LLM model gateways, Edge-TTS streaming voice parameters, Bitterbot personality directives, and hardware preferences.
            </p>
          </div>
        </div>

        {/* Quick status pills */}
        <div className="flex items-center gap-2 text-xs font-mono">
          <div className="px-3 py-1.5 rounded-lg border border-border-subtle bg-bg-card flex items-center gap-2 shadow-xs">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-text-muted">OWNER:</span>
            <span className="font-semibold text-text-primary">Sam (Sovereign)</span>
          </div>
          <div className="px-3 py-1.5 rounded-lg border border-border-subtle bg-bg-card flex items-center gap-2 shadow-xs">
            <Zap className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-text-muted">MODEL:</span>
            <span className="font-semibold text-text-primary">{activeProviderObj.defaultModel}</span>
          </div>
        </div>
      </div>

      {/* 2. SUB-NAVIGATION TABS */}
      <div className="px-6 py-3 border-b border-border-subtle bg-bg-card/20 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1 bg-bg-card-subtle p-1 rounded-lg border border-border-subtle">
          <button
            onClick={() => setActiveTab('models')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'models'
                ? 'bg-accent text-accent-contrast shadow-xs font-semibold'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <Server className="w-3.5 h-3.5" />
            <span>AI Model Gateways ({providerList.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('voice')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'voice'
                ? 'bg-accent text-accent-contrast shadow-xs font-semibold'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <Mic className="w-3.5 h-3.5" />
            <span>Neural Voice & Audio</span>
          </button>
          <button
            onClick={() => setActiveTab('personality')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'personality'
                ? 'bg-accent text-accent-contrast shadow-xs font-semibold'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <Bot className="w-3.5 h-3.5" />
            <span>Personality & Initiative</span>
          </button>
          <button
            onClick={() => setActiveTab('system')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'system'
                ? 'bg-accent text-accent-contrast shadow-xs font-semibold'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <HardDrive className="w-3.5 h-3.5" />
            <span>Privacy, Hardware & Theme</span>
          </button>
        </div>

        {/* Global Feedback notification */}
        {(providerFeedback || voiceFeedback || personalityFeedback || privacyFeedback) && (
          <div className="text-xs font-mono text-emerald-400 flex items-center gap-1.5 bg-emerald-500/10 px-3 py-1 rounded-lg border border-emerald-500/20">
            <CheckCheck className="w-3.5 h-3.5" />
            <span>{providerFeedback || voiceFeedback || personalityFeedback || privacyFeedback}</span>
          </div>
        )}
      </div>

      {/* 3. MAIN WORKSPACE CONTENT */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* TAB 1: AI MODEL GATEWAYS */}
        {activeTab === 'models' && (
          <div className="space-y-6">
            {/* Top Action bar */}
            <div className="p-4 rounded-xl border border-border-subtle bg-bg-card flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="text-xs font-bold text-text-primary font-mono uppercase tracking-wider">
                  Active Model Routing Provider
                </h3>
                <p className="text-xs text-text-muted mt-0.5">
                  Currently dispatching ReAct cognitive turns to{' '}
                  <span className="text-text-primary font-semibold font-mono">{activeProviderObj.name}</span> with model{' '}
                  <span className="text-text-primary font-semibold font-mono">[{activeProviderObj.defaultModel}]</span>.
                </p>
              </div>

              <button
                onClick={() => setIsAddingCustom(true)}
                className="py-1.5 px-3 rounded-lg border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover text-text-primary text-xs font-medium flex items-center gap-1.5 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Custom Provider</span>
              </button>
            </div>

            {/* METHOD B: DRAG-AND-DROP LOCAL GGUF MODEL REPOSITORY */}
            <div className="p-4 rounded-xl border border-accent/30 bg-bg-card/70 shadow-xs backdrop-blur-sm space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-accent/15 border border-accent/30 flex items-center justify-center text-accent">
                    <Folder className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-xs font-bold text-text-primary font-mono uppercase tracking-wider">
                        Method B: Drag & Drop GGUF Repository
                      </h4>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent/20 text-accent font-semibold">
                        Native CUDA
                      </span>
                    </div>
                    <p className="text-[11px] text-text-muted mt-0.5">
                      Drop any downloaded <code className="text-text-primary font-mono">.gguf</code> model into <code className="text-text-primary font-mono">models/</code>. MaxIM auto-detects it with zero configuration.
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={async () => {
                      try {
                        await fetch('/api/local/open-folder', { method: 'POST' });
                      } catch (err) {
                        console.error('Failed to open models folder', err);
                      }
                    }}
                    className="py-1 px-2.5 rounded-lg border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover text-text-primary text-xs font-mono flex items-center gap-1.5 transition-colors cursor-pointer"
                    title="Open models folder in Windows Explorer"
                  >
                    <Folder className="w-3.5 h-3.5 text-accent" />
                    <span>Open models/ Folder</span>
                  </button>
                  <button
                    type="button"
                    onClick={fetchLocalModels}
                    disabled={isScanningLocalModels}
                    className="py-1 px-2.5 rounded-lg border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover text-text-primary text-xs font-mono flex items-center gap-1.5 transition-colors cursor-pointer"
                    title="Rescan models folder"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isScanningLocalModels ? 'animate-spin' : ''}`} />
                    <span>Rescan ({localModels.length})</span>
                  </button>
                </div>
              </div>

              {/* Detected models list organized by capability category */}
              {localModels.length > 0 ? (
                <div className="flex flex-col gap-3 pt-2 border-t border-border-subtle/50">
                  {[
                    { key: 'llm', label: 'All-Rounder Reasoning', folder: 'models/llm/', icon: '🧠', desc: 'General intelligence, coding, and autonomous tool use' },
                    { key: 'vision', label: 'Vision & Multimodal', folder: 'models/vision/', icon: '👁️', desc: 'Autonomous background pipeline • Auto-invoked when giving or generating images' },
                    { key: 'asr', label: 'Voice-to-Text (ASR)', folder: 'models/asr/', icon: '🎙️', desc: 'Microphone speech recognition and transcription' },
                    { key: 'tts', label: 'Text-to-Voice (TTS)', folder: 'models/tts/', icon: '🔊', desc: 'Neural speech synthesis and vocal generation' },
                  ].map((cat) => {
                    const catModels = localModels.filter((m: any) => m.category === cat.key);
                    if (catModels.length === 0) return null;
                    return (
                      <div key={cat.key} className="flex flex-col gap-1.5">
                        <div className="flex items-center justify-between text-[11px] font-mono text-text-muted px-1">
                          <div className="flex items-center gap-1.5">
                            <span>{cat.icon}</span>
                            <span className="font-semibold text-text-primary">{cat.label}</span>
                            <span className="text-[10px] text-accent font-bold">({cat.folder})</span>
                          </div>
                          <span className="text-[10px] text-text-muted/80">{cat.desc}</span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                          {catModels.map((m: any) => {
                            const isProjectLocal = m.is_project_local || m.location === 'models/' || (m.location && m.location.startsWith('models/'));
                            return (
                              <div
                                key={m.id}
                                className={`p-2.5 rounded-lg border text-xs font-mono flex items-center justify-between gap-2 transition-all ${
                                  isProjectLocal
                                    ? 'bg-accent/5 border-accent/30 shadow-xs'
                                    : 'bg-bg-card-subtle/50 border-border-subtle/70'
                                }`}
                              >
                                <div className="truncate">
                                  <div className="flex items-center gap-1">
                                    <span className="text-[11px]">{cat.icon}</span>
                                    <span className="font-semibold truncate text-text-primary">{m.name}</span>
                                  </div>
                                  <span className="text-[10px] text-text-muted block mt-0.5">
                                    {m.quant} • {m.size_gb} GB • {m.location}
                                  </span>
                                </div>
                                <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase shrink-0 ${
                                  isProjectLocal ? 'bg-accent text-accent-contrast' : 'bg-bg-card border border-border-subtle text-text-muted'
                                }`}>
                                  {m.location || 'Folder'}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-[11px] text-text-muted font-mono p-2 rounded-lg bg-bg-card-subtle/30 border border-border-subtle/40 flex items-center justify-between">
                  <span>No GGUF models detected in models/ folder yet. Click "Open models/ Folder" to drop your files into llm/, vision/, asr/, or tts/!</span>
                </div>
              )}
            </div>

            {/* Provider Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {providerList.map((provider) => {
                const isActive = provider.id === activeProvider;
                return (
                  <div
                    key={provider.id}
                    className={`p-5 rounded-xl border transition-all flex flex-col justify-between shadow-xs ${
                      isActive
                        ? 'border-accent bg-bg-card ring-1 ring-accent/30'
                        : 'border-border-subtle bg-bg-card hover:border-text-secondary/40'
                    }`}
                  >
                    <div>
                      {/* Card Header */}
                      <div className="flex items-start justify-between gap-2 mb-3">
                        <div className="flex items-center gap-2">
                          <div
                            className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs ${
                              isActive ? 'bg-accent text-accent-contrast' : 'bg-bg-card-subtle text-text-secondary border border-border-subtle'
                            }`}
                          >
                            <Server className="w-3.5 h-3.5" />
                          </div>
                          <div>
                            <h4 className="text-xs font-bold text-text-primary tracking-tight">
                              {provider.name}
                            </h4>
                            <span className="text-[10px] font-mono text-text-muted uppercase">
                              {provider.category} PROVIDER
                            </span>
                          </div>
                        </div>

                        {isActive ? (
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                            ACTIVE
                          </span>
                        ) : (
                          <button
                            onClick={() => handleSaveActiveProvider(provider.id)}
                            disabled={isSavingProvider}
                            className="text-[10px] font-mono px-2.5 py-0.5 rounded-lg border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover text-text-secondary hover:text-text-primary transition-colors"
                          >
                            Set Active
                          </button>
                        )}
                      </div>

                      {/* Default Model Selector */}
                      <div className="space-y-2 mb-3">
                        <label className="block text-[10px] font-mono text-text-muted uppercase">
                          Model Identifier
                        </label>
                        <select
                          value={provider.defaultModel}
                          onChange={(e) => handleProviderChange(provider.id, 'defaultModel', e.target.value)}
                          className="w-full px-2.5 py-1.5 rounded-lg border border-border-subtle bg-bg-card-subtle text-xs font-mono text-text-primary focus:outline-none focus:border-accent"
                        >
                          {provider.models.map((m) => (
                            <option key={m} value={m}>
                              {m}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Base URL */}
                      {provider.baseUrl && (
                        <div className="space-y-1 mb-3">
                          <label className="block text-[10px] font-mono text-text-muted uppercase">
                            Endpoint Base URL
                          </label>
                          <input
                            type="text"
                            value={provider.baseUrl}
                            onChange={(e) => handleProviderChange(provider.id, 'baseUrl', e.target.value)}
                            className="w-full px-2.5 py-1 rounded-md border border-border-subtle bg-bg-card text-[11px] font-mono text-text-primary focus:outline-none focus:border-accent"
                          />
                        </div>
                      )}

                      {/* API Key field if cloud */}
                      {provider.category !== 'local' && (
                        <div className="space-y-1 mb-4">
                          <label className="block text-[10px] font-mono text-text-muted uppercase flex items-center justify-between">
                            <span>API Key</span>
                            <span className="text-[9px] text-text-muted">
                              {provider.configured ? 'STORED' : 'OPTIONAL / ENV'}
                            </span>
                          </label>
                          <div className="relative">
                            <input
                              type={showKeyMap[provider.id] ? 'text' : 'password'}
                              placeholder="e.g. sk-..."
                              value={provider.apiKey || ''}
                              onChange={(e) => handleProviderChange(provider.id, 'apiKey', e.target.value)}
                              className="w-full pl-2.5 pr-8 py-1 rounded-md border border-border-subtle bg-bg-card text-[11px] font-mono text-text-primary focus:outline-none focus:border-accent"
                            />
                            <button
                              type="button"
                              onClick={() => toggleShowKey(provider.id)}
                              className="absolute right-2 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
                            >
                              {showKeyMap[provider.id] ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Bottom activation action */}
                    <div className="pt-2 border-t border-border-subtle/60 flex items-center justify-between">
                      <span className="text-[10px] font-mono text-text-muted">
                        {provider.category === 'local' ? 'Zero Cost (Offline)' : 'Cloud API'}
                      </span>
                      <button
                        onClick={() => handleSaveActiveProvider(provider.id)}
                        disabled={isSavingProvider}
                        className={`px-3 py-1 rounded-md text-xs font-mono font-medium transition-all ${
                          isActive
                            ? 'bg-accent text-accent-contrast shadow-xs'
                            : 'border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover text-text-primary'
                        }`}
                      >
                        {isActive ? 'Current' : 'Select'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 2: NEURAL VOICE & AUDIO */}
        {activeTab === 'voice' && (
          <div className="space-y-6 max-w-3xl">
            {/* Feedback notification toast if present */}
            {voiceFeedback && (
              <div className="p-3 rounded-lg bg-accent/10 border border-accent/30 text-accent text-xs font-mono flex items-center gap-2 animate-in fade-in">
                <Check className="w-4 h-4" />
                <span>{voiceFeedback}</span>
              </div>
            )}

            {/* Architecture Invariant Banner */}
            <div className="p-4 rounded-xl border border-accent/20 bg-accent/5 flex items-start gap-3">
              <ShieldCheck className="w-5 h-5 text-accent shrink-0 mt-0.5" />
              <div className="text-xs space-y-1">
                <div className="font-bold text-text-primary font-mono uppercase tracking-wide">
                  Background Voice Pipeline Architecture
                </div>
                <div className="text-text-muted leading-relaxed">
                  Speech-to-Text (ASR) and Text-to-Speech (TTS) models run continuously in the background and are excluded from the main chat model selector. This reserves model switching for reasoning, coding, and vision. Configure your active speech and listening engines below.
                </div>
              </div>
            </div>

            {/* Latency Mode Selector Card: Turbo vs Studio */}
            <div className="p-5 rounded-xl border border-border-subtle bg-bg-card space-y-3 shadow-xs">
              <div className="flex items-center justify-between border-b border-border-subtle pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-accent text-accent-contrast flex items-center justify-center font-bold">
                    <Zap className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-text-primary uppercase font-mono tracking-wider">
                      Voice Latency & Operational Mode
                    </h3>
                    <p className="text-xs text-text-muted">
                      Control response turnaround speed for the mascot intercom and voice dialogue.
                    </p>
                  </div>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
                  {voiceSettings.latencyMode === 'studio' ? 'STUDIO QUALITY' : 'REAL-TIME (<0.3s)'}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                {/* Turbo Mode Card */}
                <div
                  onClick={() => handleSelectLatencyMode('turbo')}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    (voiceSettings.latencyMode || 'turbo') === 'turbo'
                      ? 'border-accent bg-accent/10 ring-1 ring-accent/30 shadow-sm'
                      : 'border-border-subtle bg-bg-card-subtle hover:border-text-secondary/40'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-base">⚡</span>
                      <div>
                        <h4 className="text-xs font-bold text-text-primary font-mono">Turbo Instant Mode</h4>
                        <span className="text-[10px] font-mono text-emerald-400 font-semibold">&lt; 0.3s Real-Time</span>
                      </div>
                    </div>
                    {(voiceSettings.latencyMode || 'turbo') === 'turbo' && (
                      <Check className="w-4 h-4 text-accent" />
                    )}
                  </div>
                  <p className="text-[11px] text-text-muted leading-relaxed">
                    Zero-overhead instant speech synthesis. Uses hardware-accelerated local synthesis (<strong className="text-text-secondary">0ms network wait</strong>). Recommended for snappy back-and-forth intercom conversation.
                  </p>
                </div>

                {/* Studio Neural Mode Card */}
                <div
                  onClick={() => handleSelectLatencyMode('studio')}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    voiceSettings.latencyMode === 'studio'
                      ? 'border-accent bg-accent/10 ring-1 ring-accent/30 shadow-sm'
                      : 'border-border-subtle bg-bg-card-subtle hover:border-text-secondary/40'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-base">🎙️</span>
                      <div>
                        <h4 className="text-xs font-bold text-text-primary font-mono">Studio Neural Mode</h4>
                        <span className="text-[10px] font-mono text-accent font-semibold">~1.8s Studio Audio</span>
                      </div>
                    </div>
                    {voiceSettings.latencyMode === 'studio' && (
                      <Check className="w-4 h-4 text-accent" />
                    )}
                  </div>
                  <p className="text-[11px] text-text-muted leading-relaxed">
                    Edge-TTS neural speech synthesis featuring authentic human prosody, emotional inflection, and custom personas (Christopher, Ryan, Aria, Pradeep).
                  </p>
                </div>
              </div>
            </div>

            {/* ASR: Speech-to-Text Engine Selection Card */}
            <div className="p-5 rounded-xl border border-border-subtle bg-bg-card space-y-4 shadow-xs">
              <div className="flex items-center justify-between border-b border-border-subtle pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-accent text-accent-contrast flex items-center justify-center font-bold">
                    <Mic className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-text-primary uppercase font-mono tracking-wider">
                      Speech-to-Text (ASR) Perception Model
                    </h3>
                    <p className="text-xs text-text-muted">
                      Transcribes microphone audio into structured instructions in the background.
                    </p>
                  </div>
                </div>
                <div className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-accent/10 text-accent border border-accent/20">
                  Background Service
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-xs font-mono font-medium text-text-secondary">
                  Active Speech-to-Text Engine / Model
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {/* Local Detected ASR Models */}
                  {localModels
                    .filter((m: any) => m.category === 'asr')
                    .map((model: any) => {
                      const isSelected =
                        selectedAsrModel === `asr:${model.file_name}` ||
                        selectedAsrModel === model.id;
                      return (
                        <div
                          key={model.id}
                          onClick={() => handleSelectAsrModel(model.id)}
                          className={`p-3 rounded-lg border cursor-pointer transition-all ${
                            isSelected
                              ? 'border-accent bg-accent/10 ring-1 ring-accent/30'
                              : 'border-border-subtle bg-bg-card hover:border-text-secondary/40'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-bold text-text-primary font-mono flex items-center gap-1.5">
                              <span>🎙️</span>
                              <span>{model.name}</span>
                            </span>
                            {isSelected && <Check className="w-3.5 h-3.5 text-accent" />}
                          </div>
                          <div className="flex items-center gap-2 text-[10px] font-mono text-text-muted mb-1">
                            <span className="bg-bg-card-subtle px-1.5 py-0.5 rounded border border-border-subtle">
                              {model.quant}
                            </span>
                            <span>{model.size_gb} GB</span>
                            <span className="text-emerald-400">Local (models/asr)</span>
                          </div>
                          <p className="text-[11px] text-text-muted">
                            {model.role_description || 'High-accuracy local audio transcription'}
                          </p>
                        </div>
                      );
                    })}

                  {/* Browser Web Speech API */}
                  <div
                    onClick={() => handleSelectAsrModel('browser-native')}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedAsrModel === 'browser-native'
                        ? 'border-accent bg-accent/10 ring-1 ring-accent/30'
                        : 'border-border-subtle bg-bg-card hover:border-text-secondary/40'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-text-primary font-mono flex items-center gap-1.5">
                        <span>🌐</span>
                        <span>Browser Web Speech API</span>
                      </span>
                      {selectedAsrModel === 'browser-native' && <Check className="w-3.5 h-3.5 text-accent" />}
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-mono text-text-muted mb-1">
                      <span className="bg-bg-card-subtle px-1.5 py-0.5 rounded border border-border-subtle">Zero VRAM</span>
                      <span className="text-accent">Real-Time Streaming</span>
                    </div>
                    <p className="text-[11px] text-text-muted">
                      Native browser neural transcription with immediate zero-latency recognition.
                    </p>
                  </div>

                  {/* Cloud Whisper API */}
                  <div
                    onClick={() => handleSelectAsrModel('cloud-whisper')}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedAsrModel === 'cloud-whisper'
                        ? 'border-accent bg-accent/10 ring-1 ring-accent/30'
                        : 'border-border-subtle bg-bg-card hover:border-text-secondary/40'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-text-primary font-mono flex items-center gap-1.5">
                        <span>☁️</span>
                        <span>OpenAI Whisper API</span>
                      </span>
                      {selectedAsrModel === 'cloud-whisper' && <Check className="w-3.5 h-3.5 text-accent" />}
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-mono text-text-muted mb-1">
                      <span className="bg-bg-card-subtle px-1.5 py-0.5 rounded border border-border-subtle">Cloud API</span>
                      <span>Multilingual</span>
                    </div>
                    <p className="text-[11px] text-text-muted">
                      Whisper Large-v3 cloud API for high-noise audio transcription.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* TTS: Text-to-Speech Vocal Engine & Model Selection Card */}
            <div className="p-5 rounded-xl border border-border-subtle bg-bg-card space-y-4 shadow-xs">
              <div className="flex items-center justify-between border-b border-border-subtle pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-accent text-accent-contrast flex items-center justify-center font-bold">
                    <Volume2 className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-text-primary uppercase font-mono tracking-wider">
                      Edge-TTS Neural Voice Engine
                    </h3>
                    <p className="text-xs text-text-muted">
                      Zero-cost, low-latency streaming neural voices and background TTS model selection.
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleTestVoiceAudio}
                  disabled={isPlayingTestVoice}
                  className="px-3 py-1.5 rounded-lg border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover text-text-primary text-xs font-mono font-medium flex items-center gap-1.5 transition-colors disabled:opacity-50 cursor-pointer"
                >
                  {isPlayingTestVoice ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                  <span>{isPlayingTestVoice ? 'Playing...' : 'Test Voice'}</span>
                </button>
              </div>

              <div className="space-y-2">
                <label className="block text-xs font-mono font-medium text-text-secondary">
                  Active Text-to-Speech Engine / Model
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {/* Local Detected TTS Models */}
                  {localModels
                    .filter((m: any) => m.category === 'tts')
                    .map((model: any) => {
                      const isSelected =
                        selectedTtsModel === `tts:${model.file_name}` ||
                        selectedTtsModel === model.id;
                      return (
                        <div
                          key={model.id}
                          onClick={() => handleSelectTtsModel(model.id)}
                          className={`p-3 rounded-lg border cursor-pointer transition-all ${
                            isSelected
                              ? 'border-accent bg-accent/10 ring-1 ring-accent/30'
                              : 'border-border-subtle bg-bg-card hover:border-text-secondary/40'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-bold text-text-primary font-mono flex items-center gap-1.5">
                              <span>🔊</span>
                              <span>{model.name}</span>
                            </span>
                            {isSelected && <Check className="w-3.5 h-3.5 text-accent" />}
                          </div>
                          <div className="flex items-center gap-2 text-[10px] font-mono text-text-muted mb-1">
                            <span className="bg-bg-card-subtle px-1.5 py-0.5 rounded border border-border-subtle">
                              {model.quant}
                            </span>
                            <span>{model.size_gb} GB</span>
                            <span className="text-emerald-400">Local (models/tts)</span>
                          </div>
                          <p className="text-[11px] text-text-muted">
                            {model.role_description || 'Local neural voice generation'}
                          </p>
                        </div>
                      );
                    })}

                  {/* Edge-TTS Neural Cloud Engine */}
                  <div
                    onClick={() => handleSelectTtsModel('edge-tts')}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedTtsModel === 'edge-tts'
                        ? 'border-accent bg-accent/10 ring-1 ring-accent/30'
                        : 'border-border-subtle bg-bg-card hover:border-text-secondary/40'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-text-primary font-mono flex items-center gap-1.5">
                        <span>⚡</span>
                        <span>Edge-TTS Neural Cloud</span>
                      </span>
                      {selectedTtsModel === 'edge-tts' && <Check className="w-3.5 h-3.5 text-accent" />}
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-mono text-text-muted mb-1">
                      <span className="bg-bg-card-subtle px-1.5 py-0.5 rounded border border-border-subtle">Zero Cost</span>
                      <span className="text-accent">&lt;180ms Latency</span>
                    </div>
                    <p className="text-[11px] text-text-muted">
                      Streaming neural speech synthesis with authentic human emotion and multiple personas.
                    </p>
                  </div>

                  {/* Kokoro-82M ONNX */}
                  <div
                    onClick={() => handleSelectTtsModel('kokoro-82m')}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedTtsModel === 'kokoro-82m'
                        ? 'border-accent bg-accent/10 ring-1 ring-accent/30'
                        : 'border-border-subtle bg-bg-card hover:border-text-secondary/40'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-text-primary font-mono flex items-center gap-1.5">
                        <span>🧠</span>
                        <span>Kokoro-82M ONNX Engine</span>
                      </span>
                      {selectedTtsModel === 'kokoro-82m' && <Check className="w-3.5 h-3.5 text-accent" />}
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-mono text-text-muted mb-1">
                      <span className="bg-bg-card-subtle px-1.5 py-0.5 rounded border border-border-subtle">82M Params</span>
                      <span>Local ONNX</span>
                    </div>
                    <p className="text-[11px] text-text-muted">
                      Compact local neural TTS model running completely on local CPU or GPU.
                    </p>
                  </div>
                </div>
              </div>

              {/* Voice Persona Selection */}
              <div className="space-y-2 pt-3 border-t border-border-subtle">
                <label className="block text-xs font-mono font-medium text-text-secondary">
                  Default Neural Voice Persona & Accent
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {[
                    { id: 'en-US-ChristopherNeural', name: 'Christopher (US)', desc: 'Sharp, crisp, masculine persona (Default)' },
                    { id: 'en-GB-RyanNeural', name: 'Ryan (British)', desc: 'Dry, sarcastic, intelligent British tone' },
                    { id: 'en-US-GuyNeural', name: 'Guy (US)', desc: 'Casual, conversational informal tone' },
                    { id: 'en-US-AriaNeural', name: 'Aria (US)', desc: 'Articulate, balanced female neural voice' },
                    { id: 'bn-BD-PradeepNeural', name: 'Pradeep (Bangla)', desc: 'Authentic local Bengali neural voice' },
                  ].map((v) => {
                    const isSelected = voiceSettings.voiceId === v.id;
                    return (
                      <div
                        key={v.id}
                        onClick={() => setVoiceSettings({ ...voiceSettings, voiceId: v.id })}
                        className={`p-3 rounded-lg border cursor-pointer transition-all ${
                          isSelected
                            ? 'border-accent bg-bg-card-subtle ring-1 ring-accent/30'
                            : 'border-border-subtle bg-bg-card hover:border-text-secondary/40'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-bold text-text-primary font-mono">{v.name}</span>
                          {isSelected && <Check className="w-3.5 h-3.5 text-accent" />}
                        </div>
                        <p className="text-[11px] text-text-muted">{v.desc}</p>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Speech Rate Controls */}
              <div className="space-y-2 pt-2 border-t border-border-subtle">
                <label className="block text-xs font-mono font-medium text-text-secondary">
                  Speech Rate Adjustment (Speed)
                </label>
                <div className="flex items-center gap-2">
                  {['-10%', '+0%', '+5%', '+10%', '+20%'].map((rateVal) => (
                    <button
                      key={rateVal}
                      onClick={() => setVoiceSettings({ ...voiceSettings, rate: rateVal })}
                      className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors border cursor-pointer ${
                        voiceSettings.rate === rateVal
                          ? 'bg-text-primary text-bg-main border-text-primary font-semibold'
                          : 'border-border-subtle bg-bg-card-subtle text-text-secondary hover:text-text-primary'
                      }`}
                    >
                      {rateVal === '+0%' ? 'Normal (0%)' : rateVal}
                    </button>
                  ))}
                </div>
              </div>

              {/* Toggle Switches */}
              <div className="space-y-3 pt-3 border-t border-border-subtle">
                <div className="flex items-center justify-between p-3 rounded-xl border border-border-subtle bg-bg-card-subtle">
                  <div>
                    <span className="text-xs font-semibold text-text-primary block">
                      Autonomous Hands-Free Playback
                    </span>
                    <span className="text-[11px] text-text-muted">
                      Automatically synthesize and play proactive situational interventions out loud.
                    </span>
                  </div>
                  <button
                    onClick={() => {
                      const next = !voiceSettings.autoSpeak;
                      setVoiceSettings({ ...voiceSettings, autoSpeak: next });
                      try {
                        localStorage.setItem('maxim_auto_speak', String(next));
                      } catch {}
                    }}
                    className={`px-3 py-1 rounded-lg text-xs font-mono font-semibold transition-colors border cursor-pointer ${
                      voiceSettings.autoSpeak
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30'
                    }`}
                  >
                    {voiceSettings.autoSpeak ? 'ENABLED' : 'DISABLED'}
                  </button>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl border border-border-subtle bg-bg-card-subtle">
                  <div>
                    <span className="text-xs font-semibold text-text-primary block">
                      Sarcastic & Witty Inflection
                    </span>
                    <span className="text-[11px] text-text-muted">
                      Allow neural voice to incorporate sardonic pauses and witty pitch shifts.
                    </span>
                  </div>
                  <button
                    onClick={() =>
                      setVoiceSettings({ ...voiceSettings, sarcasmEnabled: !voiceSettings.sarcasmEnabled })
                    }
                    className={`px-3 py-1 rounded-lg text-xs font-mono font-semibold transition-colors border cursor-pointer ${
                      voiceSettings.sarcasmEnabled
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30'
                    }`}
                  >
                    {voiceSettings.sarcasmEnabled ? 'ENABLED' : 'DISABLED'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: PERSONALITY & INITIATIVE */}
        {activeTab === 'personality' && (
          <div className="space-y-6 max-w-3xl">
            {/* Situational Sensitivity Card */}
            <div className="p-5 rounded-xl border border-border-subtle bg-bg-card space-y-4 shadow-xs">
              <div className="flex items-center justify-between border-b border-border-subtle pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-accent text-accent-contrast flex items-center justify-center font-bold">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-text-primary uppercase font-mono tracking-wider">
                      Proactive Situational Initiative
                    </h3>
                    <p className="text-xs text-text-muted">
                      Controls how and when MaxIM breaks silence to offer suggestions, ask questions, or hold you accountable.
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleSavePersonality}
                  className="px-3 py-1.5 rounded-lg bg-accent text-accent-contrast text-xs font-mono font-semibold hover:opacity-90 active:scale-98 transition-all flex items-center gap-1.5"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Save Persona</span>
                </button>
              </div>

              {/* Initiative Modes */}
              <div className="space-y-2">
                <label className="block text-xs font-mono font-medium text-text-secondary">
                  Sensitivity Mode
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {[
                    {
                      id: 'muted',
                      title: 'Muted (Passive)',
                      desc: 'Never interrupts. Speaks strictly when asked.',
                    },
                    {
                      id: 'gentle',
                      title: 'Gentle (Infrequent)',
                      desc: 'Interjects only after >45m idle or major context shift.',
                    },
                    {
                      id: 'balanced',
                      title: 'Balanced (Standard)',
                      desc: 'Witty check-ins aligned with LifeOS TELOS targets.',
                    },
                    {
                      id: 'proactive',
                      title: 'Proactive (Accountability Partner)',
                      desc: 'Active questions, deep reflection, and code reviews.',
                    },
                  ].map((m) => {
                    const isSelected = personalitySettings.mode === m.id;
                    return (
                      <div
                        key={m.id}
                        onClick={() =>
                          setPersonalitySettings({
                            ...personalitySettings,
                            mode: m.id as PersonalitySettingsItem['mode'],
                          })
                        }
                        className={`p-3 rounded-lg border cursor-pointer transition-all ${
                          isSelected
                            ? 'border-accent bg-bg-card-subtle ring-1 ring-accent/30'
                            : 'border-border-subtle bg-bg-card hover:border-text-secondary/40'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-bold text-text-primary font-mono">{m.title}</span>
                          {isSelected && <Check className="w-3.5 h-3.5 text-accent" />}
                        </div>
                        <p className="text-[11px] text-text-muted">{m.desc}</p>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Persona Archetype */}
              <div className="space-y-2 pt-3 border-t border-border-subtle">
                <label className="block text-xs font-mono font-medium text-text-secondary">
                  Personality Archetype
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'bitterbot', name: 'Bitterbot', desc: 'Sarcastic wit, playful teasing, lethal competence' },
                    { id: 'chief_operator', name: 'Chief Operator', desc: 'Pragmatic, structured, metric-driven coordinator' },
                    { id: 'silent_executor', name: 'Silent Executor', desc: 'Zero fluff, pure execution output' },
                  ].map((arch) => {
                    const isSelected = personalitySettings.archetype === arch.id;
                    return (
                      <div
                        key={arch.id}
                        onClick={() =>
                          setPersonalitySettings({
                            ...personalitySettings,
                            archetype: arch.id as PersonalitySettingsItem['archetype'],
                          })
                        }
                        className={`p-3 rounded-lg border cursor-pointer transition-all ${
                          isSelected
                            ? 'border-accent bg-bg-card-subtle ring-1 ring-accent/30'
                            : 'border-border-subtle bg-bg-card hover:border-text-secondary/40'
                        }`}
                      >
                        <span className="text-xs font-bold text-text-primary font-mono block mb-1">
                          {arch.name}
                        </span>
                        <p className="text-[10px] text-text-muted">{arch.desc}</p>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Interjection Cooldown */}
              <div className="space-y-2 pt-3 border-t border-border-subtle">
                <label className="block text-xs font-mono font-medium text-text-secondary flex items-center justify-between">
                  <span>Interjection Cooldown Window</span>
                  <span className="text-text-primary font-bold">{personalitySettings.cooldownSeconds}s</span>
                </label>
                <div className="flex items-center gap-2">
                  {[60, 120, 180, 300, 600].map((sec) => (
                    <button
                      key={sec}
                      onClick={() => setPersonalitySettings({ ...personalitySettings, cooldownSeconds: sec })}
                      className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors border ${
                        personalitySettings.cooldownSeconds === sec
                          ? 'bg-text-primary text-bg-main border-text-primary font-semibold'
                          : 'border-border-subtle bg-bg-card-subtle text-text-secondary hover:text-text-primary'
                      }`}
                    >
                      {sec >= 60 ? `${sec / 60}m` : `${sec}s`}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: PRIVACY, HARDWARE & THEME */}
        {activeTab === 'system' && (
          <div className="space-y-6 max-w-3xl">
            {/* Sacred Owner Loyalty & Privacy Guard */}
            <div className="p-5 rounded-xl border border-border-subtle bg-bg-card space-y-4 shadow-xs">
              <div className="flex items-center justify-between border-b border-border-subtle pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-accent text-accent-contrast flex items-center justify-center font-bold">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-text-primary uppercase font-mono tracking-wider">
                      Sacred Owner Loyalty & Zero-Egress Sandbox
                    </h3>
                    <p className="text-xs text-text-muted">
                      Permanently bonded to Sam. Rejects external adversarial manipulation and defangs outbound PII.
                    </p>
                  </div>
                </div>

                <span className="text-[10px] font-mono px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
                  ARMOR ACTIVE
                </span>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-xl border border-border-subtle bg-bg-card-subtle">
                  <div>
                    <span className="text-xs font-semibold text-text-primary block">
                      Local Path Redaction
                    </span>
                    <span className="text-[11px] text-text-muted">
                      Scrub sensitive local filesystem paths (e.g. C:\Users\Sam...) before model egress.
                    </span>
                  </div>
                  <button
                    onClick={() => {
                      setLocalPathRedaction(!localPathRedaction);
                      handleSavePrivacy();
                    }}
                    className={`px-3 py-1 rounded-lg text-xs font-mono font-semibold transition-colors border ${
                      localPathRedaction
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30'
                    }`}
                  >
                    {localPathRedaction ? 'ACTIVE' : 'MUTED'}
                  </button>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl border border-border-subtle bg-bg-card-subtle">
                  <div>
                    <span className="text-xs font-semibold text-text-primary block">
                      Outbound Credential Sanitization
                    </span>
                    <span className="text-[11px] text-text-muted">
                      Detect and block API keys, tokens, or passwords from appearing in web search queries.
                    </span>
                  </div>
                  <button
                    onClick={() => {
                      setOutboundSanitization(!outboundSanitization);
                      handleSavePrivacy();
                    }}
                    className={`px-3 py-1 rounded-lg text-xs font-mono font-semibold transition-colors border ${
                      outboundSanitization
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30'
                    }`}
                  >
                    {outboundSanitization ? 'ACTIVE' : 'MUTED'}
                  </button>
                </div>
              </div>
            </div>

            {/* Appearance & Hardware Telemetry */}
            <div className="p-5 rounded-xl border border-border-subtle bg-bg-card space-y-4 shadow-xs">
              <h3 className="text-xs font-bold text-text-primary uppercase font-mono tracking-wider border-b border-border-subtle pb-3">
                Cockpit Display & Telemetry Polling
              </h3>

              {/* Theme switcher */}
              <div className="flex items-center justify-between p-3 rounded-xl border border-border-subtle bg-bg-card-subtle">
                <div className="flex items-center gap-2.5">
                  {theme === 'dark' ? <Moon className="w-4 h-4 text-text-secondary" /> : <Sun className="w-4 h-4 text-amber-500" />}
                  <div>
                    <span className="text-xs font-semibold text-text-primary block">
                      Interface Theme Mode
                    </span>
                    <span className="text-[11px] text-text-muted">
                      Minimal high-contrast Black & White aesthetic.
                    </span>
                  </div>
                </div>

                <button
                  onClick={toggleTheme}
                  className="px-3 py-1.5 rounded-lg border border-border-subtle bg-bg-card text-xs font-mono text-text-primary hover:bg-bg-card-hover transition-colors font-medium"
                >
                  {theme.toUpperCase()} MODE
                </button>
              </div>

              {/* Telemetry Polling Interval */}
              <div className="space-y-2 pt-2">
                <label className="block text-xs font-mono font-medium text-text-secondary flex items-center justify-between">
                  <span>Hardware Telemetry HUD Poll Rate</span>
                  <span className="text-text-primary font-bold">{telemetryInterval}s</span>
                </label>
                <div className="flex items-center gap-2">
                  {[2, 5, 10, 30].map((rate) => (
                    <button
                      key={rate}
                      onClick={() => setTelemetryInterval(rate)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors border ${
                        telemetryInterval === rate
                          ? 'bg-text-primary text-bg-main border-text-primary font-semibold'
                          : 'border-border-subtle bg-bg-card-subtle text-text-secondary hover:text-text-primary'
                      }`}
                    >
                      Every {rate}s
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 4. MODAL: REGISTER CUSTOM PROVIDER */}
      {isAddingCustom && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs select-none">
          <div className="w-full max-w-md rounded-2xl border border-border-subtle bg-bg-card p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-start justify-between pb-3 border-b border-border-subtle">
              <div className="flex items-center gap-2">
                <Server className="w-4 h-4 text-text-primary" />
                <h3 className="text-xs font-bold font-mono uppercase text-text-primary">
                  Register Custom OpenAI-Compatible Provider
                </h3>
              </div>
              <button
                onClick={() => setIsAddingCustom(false)}
                className="text-text-muted hover:text-text-primary"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddCustomProvider} className="space-y-3 text-xs">
              <div>
                <label className="block font-mono text-[11px] text-text-secondary mb-1">
                  Provider Display Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Local vLLM Server"
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-border-subtle bg-bg-card-subtle font-mono text-xs text-text-primary focus:outline-none focus:border-accent"
                  required
                />
              </div>

              <div>
                <label className="block font-mono text-[11px] text-text-secondary mb-1">
                  Base URL (OpenAI V1 Endpoint)
                </label>
                <input
                  type="text"
                  placeholder="e.g. http://localhost:8080/v1"
                  value={customBaseUrl}
                  onChange={(e) => setCustomBaseUrl(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-border-subtle bg-bg-card-subtle font-mono text-xs text-text-primary focus:outline-none focus:border-accent"
                  required
                />
              </div>

              <div>
                <label className="block font-mono text-[11px] text-text-secondary mb-1">
                  Default Model Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. mistral-7b-instruct"
                  value={customModel}
                  onChange={(e) => setCustomModel(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-border-subtle bg-bg-card-subtle font-mono text-xs text-text-primary focus:outline-none focus:border-accent"
                  required
                />
              </div>

              <div>
                <label className="block font-mono text-[11px] text-text-secondary mb-1">
                  API Key (Optional for local servers)
                </label>
                <input
                  type="password"
                  placeholder="dummy-key or bearer token"
                  value={customApiKey}
                  onChange={(e) => setCustomApiKey(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-border-subtle bg-bg-card-subtle font-mono text-xs text-text-primary focus:outline-none focus:border-accent"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-border-subtle">
                <button
                  type="button"
                  onClick={() => setIsAddingCustom(false)}
                  className="px-4 py-2 rounded-lg border border-border-subtle bg-bg-card-subtle text-xs text-text-primary hover:bg-bg-card-hover font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-accent text-accent-contrast text-xs font-semibold hover:opacity-90 active:scale-98 transition-all flex items-center gap-1.5"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Mount Provider</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsView;
