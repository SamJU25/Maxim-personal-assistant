import React, { useState, useEffect, useRef } from 'react';
import {
  Mic,
  MicOff,
  Volume2,
  Brain,
  Search,
  CheckCircle2,
  Zap,
  AlertTriangle,
  Radio,
} from 'lucide-react';

export type MascotState =
  | 'idle'
  | 'listening'
  | 'thinking'
  | 'searching'
  | 'executing'
  | 'talking'
  | 'success'
  | 'alert';

interface MascotStageProps {
  onOpenUplinkModal?: () => void;
  isCompact?: boolean;
  state?: MascotState;
  statusMessage?: string;
  onStateChange?: (state: MascotState) => void;
}

const stateConfig: Record<
  MascotState,
  {
    label: string;
    icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
    accentColor: string;
    glowColor: string;
    defaultMessage: string;
  }
> = {
  idle: {
    label: 'VIGILANT • READY',
    icon: Radio,
    accentColor: '#00d992',
    glowColor: 'rgba(0, 217, 146, 0.4)',
    defaultMessage: 'Neural loop online • Standing by for voice or text',
  },
  listening: {
    label: 'AUDIO PERCEPTION ACTIVE',
    icon: Volume2,
    accentColor: '#00f2fe',
    glowColor: 'rgba(0, 242, 254, 0.5)',
    defaultMessage: 'Audio perception active • Listening for voice directive...',
  },
  thinking: {
    label: 'NEURAL REASONING',
    icon: Brain,
    accentColor: '#818cf8',
    glowColor: 'rgba(129, 140, 248, 0.45)',
    defaultMessage: 'Evaluating directive through 5-layer memory context...',
  },
  searching: {
    label: 'VAULT & GRAPH SCANNING',
    icon: Search,
    accentColor: '#38bdf8',
    glowColor: 'rgba(56, 189, 248, 0.45)',
    defaultMessage: 'Scanning Obsidian vault, knowledge graph & web feeds...',
  },
  executing: {
    label: 'EXECUTING FASTMCP TOOL',
    icon: Zap,
    accentColor: '#2dd4bf',
    glowColor: 'rgba(45, 212, 191, 0.5)',
    defaultMessage: 'Executing FastMCP tool & validating receipts...',
  },
  talking: {
    label: 'SYNTHESIZING SPEECH',
    icon: Volume2,
    accentColor: '#34d399',
    glowColor: 'rgba(52, 211, 153, 0.5)',
    defaultMessage: 'Synthesizing neural speech via local Kokoro-82M...',
  },
  success: {
    label: 'DIRECTIVE VERIFIED',
    icon: CheckCircle2,
    accentColor: '#10b981',
    glowColor: 'rgba(16, 185, 129, 0.6)',
    defaultMessage: 'Directive verified and executed successfully.',
  },
  alert: {
    label: 'ATTENTION REQUIRED',
    icon: AlertTriangle,
    accentColor: '#f59e0b',
    glowColor: 'rgba(245, 158, 11, 0.5)',
    defaultMessage: 'Subsystem parameter alert • Auto-resolving...',
  },
};

export const cleanVoiceUtterance = (text: string): string => {
  if (!text) return '';
  let cleaned = text;
  cleaned = cleaned.replace(/\b(magazine|maximum|max in|max aim|mexican|macsim|maxine|magsim|max im|max it|make scene|mack sim|maksim)\b/gi, 'MaxIM');
  cleaned = cleaned.replace(/\b(tell us|tel us|tell os|tel os)\b/gi, 'TELOS');
  cleaned = cleaned.replace(/\b(life os|life of|life us)\b/gi, 'LifeOS');
  cleaned = cleaned.replace(/\b(bitter bot|peter bot|better bot)\b/gi, 'Bitterbot');
  cleaned = cleaned.replace(/\b(open human)\b/gi, 'OpenHuman');
  cleaned = cleaned.replace(/\b(zylos|zilos|xylos)\b/gi, 'Zylos');
  cleaned = cleaned.replace(/\b(hermes|her mess)\b/gi, 'Hermes');
  return cleaned.trim();
};

export const MascotStage: React.FC<MascotStageProps> = ({
  isCompact = false,
  state: controlledState,
  statusMessage,
  onStateChange,
}) => {
  const [internalState, setInternalState] = useState<MascotState>('idle');
  const [customStatus, setCustomStatus] = useState<string | null>(null);
  const [blink, setBlink] = useState<boolean>(false);
  const [glanceX, setGlanceX] = useState<number>(0);
  const [speechWave, setSpeechWave] = useState<number[]>([6, 12, 22, 28, 20, 10, 5]);
  const [earLevels, setEarLevels] = useState<[number, number, number]>([1, 2, 1]);

  const mascotState = controlledState ?? internalState;

  const recognitionRef = useRef<any>(null);
  const lastHeardRef = useRef<string>('');
  const silenceTimerRef = useRef<any>(null);
  const recognitionActiveRef = useRef<boolean>(false);

  const setMascotState = (st: MascotState, msg?: string) => {
    setInternalState(st);
    if (msg) setCustomStatus(msg);
    onStateChange?.(st);
  };

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const stopListeningAndSubmit = async () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    recognitionActiveRef.current = false;
    try {
      recognitionRef.current?.stop();
    } catch {}

    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== 'inactive') {
      try {
        recorder.stop();
      } catch {}
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    const selectedAsrModel = (() => {
      try {
        return localStorage.getItem('maxim_selected_asr_model') || 'asr:Qwen3-ASR-1.7B-F16.gguf';
      } catch {
        return 'asr:Qwen3-ASR-1.7B-F16.gguf';
      }
    })();

    // 1. If user selected a local ASR model and audio was captured, send to local ASR engine
    if (selectedAsrModel !== 'browser-native' && audioChunksRef.current.length > 0) {
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      audioChunksRef.current = [];

      if (audioBlob.size > 2000) {
        setMascotState('thinking', 'Local ASR model transcribing audio...');
        try {
          const formData = new FormData();
          formData.append('file', audioBlob, 'recording.webm');
          const res = await fetch('/api/voice/transcribe', {
            method: 'POST',
            body: formData,
          });
          if (res.ok) {
            const data = await res.json();
            const transcribed = cleanVoiceUtterance((data.text || '').trim());
            if (transcribed) {
              setMascotState('thinking', `Processing voice directive: "${transcribed}"`);
              window.dispatchEvent(
                new CustomEvent('maxim:open-drawer-tab', { detail: { tab: 'chat' } })
              );
              window.dispatchEvent(
                new CustomEvent('maxim:send-prompt', { detail: { prompt: transcribed, source: 'voice' } })
              );
              lastHeardRef.current = '';
              return;
            }
          }
        } catch (asrErr) {
          console.error('Local ASR transcription error:', asrErr);
        }
      }
    }

    // 2. Web Speech / Fallback path with proper noun correction
    const spoken = cleanVoiceUtterance(lastHeardRef.current.trim());
    if (spoken) {
      setMascotState('thinking', `Processing voice directive: "${spoken}"`);
      window.dispatchEvent(
        new CustomEvent('maxim:open-drawer-tab', { detail: { tab: 'chat' } })
      );
      window.dispatchEvent(
        new CustomEvent('maxim:send-prompt', { detail: { prompt: spoken, source: 'voice' } })
      );
      lastHeardRef.current = '';
      audioChunksRef.current = [];
      return;
    }

    setMascotState('idle', 'Neural loop online • Standing by for voice or text');
  };

  const toggleIntercom = async () => {
    // Immediately stop any active speech synthesis so MaxIM doesn't talk over the user
    window.dispatchEvent(new CustomEvent('maxim:stop-speaking'));

    if (mascotState === 'listening' || recognitionActiveRef.current) {
      stopListeningAndSubmit();
      return;
    }

    audioChunksRef.current = [];

    // 1. Request microphone permission explicitly via getUserMedia
    let stream: MediaStream;
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Microphone audio capture not supported by browser');
      }
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
    } catch (permErr: any) {
      console.warn('Microphone permission blocked:', permErr);
      setMascotState('alert', 'Microphone blocked: Please allow mic access in your browser address bar');
      setTimeout(() => {
        setMascotState('idle', 'Neural loop online • Standing by');
      }, 4500);
      return;
    }

    // 2. Start local MediaRecorder to capture audio for local ASR
    try {
      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };
      recorder.start(200);
      mediaRecorderRef.current = recorder;
    } catch (recErr) {
      console.warn('MediaRecorder init failed, relying on speech recognition:', recErr);
    }

    recognitionActiveRef.current = true;
    lastHeardRef.current = '';
    setMascotState('listening', 'Listening... Speak your directive now');

    // 3. Attach Web Speech API as live caption enhancement if available
    const SpeechRec =
      typeof window !== 'undefined'
        ? (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
        : null;

    if (SpeechRec) {
      try {
        const recognition = new SpeechRec();
        recognition.lang = 'en-US';
        recognition.interimResults = true;
        recognition.continuous = true;

        recognition.onresult = (ev: any) => {
          let interim = '';
          let final = '';
          for (let i = 0; i < ev.results.length; ++i) {
            if (ev.results[i].isFinal) {
              final += ev.results[i][0].transcript;
            } else {
              interim += ev.results[i][0].transcript;
            }
          }
          const rawSpoken = (final || interim).trim();
          const spoken = cleanVoiceUtterance(rawSpoken);
          if (spoken) {
            lastHeardRef.current = spoken;
            setCustomStatus(`Hearing: "${spoken}"`);

            if (silenceTimerRef.current) {
              clearTimeout(silenceTimerRef.current);
            }
            silenceTimerRef.current = setTimeout(() => {
              if (recognitionActiveRef.current) {
                stopListeningAndSubmit();
              }
            }, 1800);
          }
        };

        recognition.onerror = (ev: any) => {
          console.warn('Mascot speech recognition event:', ev.error);
          if (ev.error === 'no-speech') {
            return;
          }
          if (ev.error === 'network') {
            // In Brave or offline: Web Speech network error, but local MediaRecorder is recording!
            setCustomStatus('Recording audio for local ASR model • Click to finish');
            return;
          }
          if (ev.error === 'not-allowed' || ev.error === 'audio-capture') {
            recognitionActiveRef.current = false;
            setMascotState('alert', 'Microphone permission denied. Allow mic access in browser address bar.');
            setTimeout(() => {
              setMascotState('idle', 'Neural loop online • Standing by');
            }, 4500);
            return;
          }
        };

        recognition.onend = () => {
          if (recognitionActiveRef.current && lastHeardRef.current) {
            stopListeningAndSubmit();
          }
        };

        recognitionRef.current = recognition;
        recognition.start();
      } catch (err) {
        console.warn('Speech recognition helper not available, using local ASR recording:', err);
      }
    } else {
      setCustomStatus('Recording audio for local ASR model • Click to finish');
    }
  };

  // Listen for global custom events from chat, tools, or memory
  useEffect(() => {
    const handleEvent = (e: Event) => {
      const detail = (e as CustomEvent<{ state: MascotState; message?: string }>).detail;
      if (detail?.state) {
        setInternalState(detail.state);
        if (detail.message) {
          setCustomStatus(detail.message);
        }
      }
    };
    window.addEventListener('maxim:mascot-state', handleEvent);
    return () => window.removeEventListener('maxim:mascot-state', handleEvent);
  }, []);

  // Natural organic blinking with occasional double-blink
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setBlink(true);
      setTimeout(() => {
        setBlink(false);
        // 25% chance of double blink
        if (Math.random() < 0.25) {
          setTimeout(() => {
            setBlink(true);
            setTimeout(() => setBlink(false), 140);
          }, 100);
        }
      }, 160);
    }, 4200);

    return () => clearInterval(blinkInterval);
  }, []);

  // Sentient micro-glances when idling
  useEffect(() => {
    if (mascotState !== 'idle') {
      setGlanceX(0);
      return;
    }
    const glanceInterval = setInterval(() => {
      const directions = [-5, 0, 5, 0];
      const nextGlance = directions[Math.floor(Math.random() * directions.length)];
      setGlanceX(nextGlance);
      // Return to center after 1.4s
      if (nextGlance !== 0) {
        setTimeout(() => setGlanceX(0), 1400);
      }
    }, 6200);

    return () => clearInterval(glanceInterval);
  }, [mascotState]);

  // Audio-reactive mouth articulation loop when talking
  useEffect(() => {
    if (mascotState !== 'talking') return;
    const waveInterval = setInterval(() => {
      setSpeechWave([
        Math.floor(Math.random() * 8) + 4,
        Math.floor(Math.random() * 16) + 6,
        Math.floor(Math.random() * 24) + 10,
        Math.floor(Math.random() * 30) + 12,
        Math.floor(Math.random() * 24) + 10,
        Math.floor(Math.random() * 16) + 6,
        Math.floor(Math.random() * 8) + 4,
      ]);
    }, 90);
    return () => clearInterval(waveInterval);
  }, [mascotState]);

  // Ear Pod dynamic levels animation
  useEffect(() => {
    if (mascotState === 'idle') {
      setEarLevels([1, 2, 1]);
      return;
    }
    const levelInterval = setInterval(() => {
      setEarLevels([
        Math.floor(Math.random() * 3) + 1,
        Math.floor(Math.random() * 3) + 1,
        Math.floor(Math.random() * 3) + 1,
      ]);
    }, 140);
    return () => clearInterval(levelInterval);
  }, [mascotState]);

  const currentConfig = stateConfig[mascotState] ?? stateConfig.idle;
  const activeMessage = statusMessage ?? customStatus ?? currentConfig.defaultMessage;
  const StateIcon = currentConfig.icon;

  // Render Left or Right Eye Graphic with Multi-Layered OLED Optics
  const renderEye = (isLeft: boolean) => {
    const isSearching = mascotState === 'searching';
    const isThinking = mascotState === 'thinking';
    const isSuccess = mascotState === 'success';
    const isListening = mascotState === 'listening';
    const isExecuting = mascotState === 'executing';
    const isAlert = mascotState === 'alert';

    return (
      <div
        className="relative flex items-center justify-center transition-all duration-300 select-none"
        style={{
          transform: `translateX(${glanceX}px)`,
        }}
      >
        {/* Soft Outer OLED Glow Bloom */}
        <div
          className="absolute -inset-2 rounded-full opacity-60 blur-md pointer-events-none transition-all duration-300"
          style={{ backgroundColor: currentConfig.accentColor }}
        />

        {/* 1. Blink State */}
        {blink ? (
          <div
            className="w-8 h-1 rounded-full opacity-80 shadow-xs transition-all duration-100"
            style={{ backgroundColor: currentConfig.accentColor }}
          />
        ) : isSuccess ? (
          /* 2. Success State: Joyful Curved Smiling Crescent (^ ^) + Sparkle Star */
          <div className="relative flex items-center justify-center">
            <div
              className="w-8 h-6 rounded-t-full border-t-[5px] border-x-[4px] border-b-0 bg-transparent transition-all duration-200"
              style={{
                borderColor: currentConfig.accentColor,
                filter: `drop-shadow(0 0 10px ${currentConfig.glowColor})`,
              }}
            />
            {/* Sparkle Star on Right Eye */}
            {!isLeft && (
              <span className="absolute -top-3.5 -right-3 text-xs text-white animate-gleam-twinkle pointer-events-none">
                ✦
              </span>
            )}
          </div>
        ) : isSearching ? (
          /* 3. Searching State: Streamlined Radar Aperture with Data Pulses */
          <div
            className="w-11 h-4 rounded-full flex items-center justify-center relative overflow-hidden transition-all duration-200"
            style={{
              backgroundColor: currentConfig.accentColor,
              boxShadow: `0 0 18px ${currentConfig.glowColor}`,
            }}
          >
            {/* Internal data stream sweep */}
            <div className="absolute inset-0 bg-white/40 animate-radar-sweep" />
            <span className="w-1.5 h-1.5 rounded-full bg-white shadow-xs z-10" />
          </div>
        ) : isExecuting ? (
          /* 4. Executing State: Cybernetic Digital Bracket HUD [ • ] */
          <div
            className="w-9 h-11 rounded-lg border-2 flex items-center justify-center relative font-mono text-[10px] transition-all duration-200"
            style={{
              borderColor: currentConfig.accentColor,
              boxShadow: `0 0 18px ${currentConfig.glowColor}, inset 0 0 8px ${currentConfig.glowColor}`,
              backgroundColor: 'rgba(5, 10, 16, 0.7)',
            }}
          >
            {/* Corner Crosshair Ticks */}
            <span
              className="w-3 h-3 rounded-full animate-ping opacity-75"
              style={{ backgroundColor: currentConfig.accentColor }}
            />
            <span
              className="w-2.5 h-2.5 rounded-full absolute"
              style={{ backgroundColor: currentConfig.accentColor }}
            />
            {/* Tech Corner Markers */}
            <span className="absolute -top-1 -left-1 text-[8px] font-bold text-white/70">⌜</span>
            <span className="absolute -bottom-1 -right-1 text-[8px] font-bold text-white/70">⌟</span>
          </div>
        ) : isThinking ? (
          /* 5. Thinking State: Analytical Tilted Gaze with Rotating Neural Reticle */
          <div
            className={`w-8 h-10 rounded-2xl flex items-center justify-center relative transition-all duration-300 ${
              isLeft ? 'rotate-6 scale-95' : '-rotate-6 scale-100'
            }`}
            style={{
              backgroundColor: currentConfig.accentColor,
              boxShadow: `0 0 20px ${currentConfig.glowColor}`,
            }}
          >
            {/* Rotating Neural Core Reticle */}
            <div className="w-4 h-4 rounded-full border border-dashed border-white/80 animate-spin" />
            <span className="w-1.5 h-1.5 rounded-full bg-white absolute top-1 left-1.5 shadow-xs" />
          </div>
        ) : isAlert ? (
          /* 6. Alert State: Angled Concerned Brow */
          <div
            className={`w-8 h-10 rounded-2xl flex items-center justify-center relative transition-all duration-200 ${
              isLeft ? '-rotate-12' : 'rotate-12'
            }`}
            style={{
              backgroundColor: currentConfig.accentColor,
              boxShadow: `0 0 20px ${currentConfig.glowColor}`,
            }}
          >
            <span className="w-2 h-2 rounded-full bg-white absolute top-1.5 left-1.5 shadow-xs" />
          </div>
        ) : (
          /* 7. Idle & Listening States: Luminous Curvature OLED Pill Eyes */
          <div
            className={`relative flex items-center justify-center rounded-[20px] transition-all duration-200 ${
              isCompact ? 'w-6 h-9' : 'w-8.5 h-12'
            } ${isListening ? 'scale-110' : ''}`}
            style={{
              background: `linear-gradient(180deg, #ffffff 0%, ${currentConfig.accentColor} 45%, #054a35 100%)`,
              boxShadow: `0 0 22px ${currentConfig.glowColor}, inset 0 2px 4px rgba(255,255,255,0.7)`,
            }}
          >
            {/* Specular Catch-light 1: Crisp Top-Left Glint */}
            <span className="w-2 h-2.5 rounded-full bg-white absolute top-1.5 left-1.5 shadow-xs" />

            {/* Specular Catch-light 2: Ambient Bottom Reflection */}
            <span className="w-3.5 h-1 rounded-full bg-white/40 absolute bottom-1.5 right-1.5 blur-[0.5px]" />
          </div>
        )}
      </div>
    );
  };

  // Shared Mascot Graphic (Obsidian Chassis, Machined Ear Pods, Curved OLED Visor)
  const renderMascotGraphic = (compact: boolean) => (
    <div
      onClick={() => {
        // Playful interactive touch
        setMascotState('success', 'Kai is online, vigilant, and synchronized!');
        setTimeout(() => setMascotState('idle'), 2200);
      }}
      className="relative flex flex-col items-center animate-float-hover my-2 cursor-pointer group"
      title="Click Kai to interact"
    >
      {/* Aerodynamic Aerospace Obsidian Chassis Shell */}
      <div
        className={`rounded-[36px] border border-white/10 bg-gradient-to-b from-[#222834] via-[#141822] to-[#0a0d12] shadow-[0_20px_50px_-10px_rgba(0,0,0,0.9),inset_0_1px_2px_rgba(255,255,255,0.25)] flex flex-col items-center justify-center relative p-2.5 transition-all duration-300 group-hover:border-accent/40 ${
          compact ? 'w-56 h-34' : 'w-80 h-48'
        }`}
      >
        {/* Precision Crown Specular Highlight Rim */}
        <div className="absolute top-0 inset-x-10 h-[1.5px] bg-gradient-to-r from-transparent via-white/40 to-transparent" />

        {/* Left Machined Acoustic Sensor Pod */}
        <div
          className={`absolute -left-3.5 top-1/2 -translate-y-1/2 w-4 h-14 rounded-l-2xl border border-white/10 bg-[#121620] flex items-center justify-center gap-0.5 p-1 transition-all duration-300 shadow-lg ${
            mascotState !== 'idle' ? 'shadow-[0_0_14px_var(--accent-glow)]' : ''
          }`}
          style={{
            borderColor: mascotState !== 'idle' ? currentConfig.accentColor : undefined,
          }}
        >
          {/* 3 Vertical Dynamic LED Level Bars */}
          <div className="flex flex-col gap-1 items-center">
            <span
              className="w-1.5 rounded-full transition-all duration-150"
              style={{
                height: `${earLevels[0] * 3.5}px`,
                backgroundColor: currentConfig.accentColor,
                boxShadow: `0 0 6px ${currentConfig.glowColor}`,
              }}
            />
            <span
              className="w-1.5 rounded-full transition-all duration-150"
              style={{
                height: `${earLevels[1] * 3.5}px`,
                backgroundColor: currentConfig.accentColor,
                boxShadow: `0 0 6px ${currentConfig.glowColor}`,
              }}
            />
            <span
              className="w-1.5 rounded-full transition-all duration-150"
              style={{
                height: `${earLevels[2] * 3.5}px`,
                backgroundColor: currentConfig.accentColor,
                boxShadow: `0 0 6px ${currentConfig.glowColor}`,
              }}
            />
          </div>
        </div>

        {/* Right Machined Acoustic Sensor Pod */}
        <div
          className={`absolute -right-3.5 top-1/2 -translate-y-1/2 w-4 h-14 rounded-r-2xl border border-white/10 bg-[#121620] flex items-center justify-center gap-0.5 p-1 transition-all duration-300 shadow-lg ${
            mascotState !== 'idle' ? 'shadow-[0_0_14px_var(--accent-glow)]' : ''
          }`}
          style={{
            borderColor: mascotState !== 'idle' ? currentConfig.accentColor : undefined,
          }}
        >
          {/* 3 Vertical Dynamic LED Level Bars */}
          <div className="flex flex-col gap-1 items-center">
            <span
              className="w-1.5 rounded-full transition-all duration-150"
              style={{
                height: `${earLevels[2] * 3.5}px`,
                backgroundColor: currentConfig.accentColor,
                boxShadow: `0 0 6px ${currentConfig.glowColor}`,
              }}
            />
            <span
              className="w-1.5 rounded-full transition-all duration-150"
              style={{
                height: `${earLevels[1] * 3.5}px`,
                backgroundColor: currentConfig.accentColor,
                boxShadow: `0 0 6px ${currentConfig.glowColor}`,
              }}
            />
            <span
              className="w-1.5 rounded-full transition-all duration-150"
              style={{
                height: `${earLevels[0] * 3.5}px`,
                backgroundColor: currentConfig.accentColor,
                boxShadow: `0 0 6px ${currentConfig.glowColor}`,
              }}
            />
          </div>
        </div>

        {/* Deep Curved 3D OLED Visor Glass */}
        <div
          className={`rounded-[26px] border border-white/10 bg-[#06080d] flex flex-col items-center justify-between relative overflow-hidden transition-all duration-300 p-3 shadow-[inset_0_0_30px_rgba(0,0,0,0.95)] ${
            compact ? 'w-46 h-24' : 'w-68 h-36'
          }`}
          style={{
            boxShadow: `inset 0 0 24px rgba(0,0,0,0.9), 0 0 24px ${currentConfig.glowColor}`,
          }}
        >
          {/* Specular Diagonal Corner Lens Flare (Curved Glass Optics) */}
          <div className="absolute -top-12 -left-12 w-32 h-32 bg-gradient-to-br from-white/15 via-white/3 to-transparent rounded-full blur-sm pointer-events-none" />

          {/* Micro-Grid Scanline Texture */}
          <div
            className="absolute inset-0 pointer-events-none opacity-10 bg-[linear-gradient(rgba(255,255,255,0.08)_1px,transparent_1px)] bg-[size:100%_3px]"
          />

          {/* Radar Sweep Effect (Active in Searching) */}
          {mascotState === 'searching' && (
            <div className="absolute inset-y-0 w-12 bg-gradient-to-r from-transparent via-cyan-400/25 to-transparent animate-radar-sweep pointer-events-none" />
          )}

          {/* OLED Eyes Layer */}
          <div className="flex items-center justify-center gap-8 my-auto z-10">
            {renderEye(true)}
            {renderEye(false)}
          </div>

          {/* OLED Acoustic Mouth & Dynamic Equalizer Layer */}
          <div className="h-3 flex items-center justify-center mt-auto z-10">
            {mascotState === 'talking' ? (
              /* Real-time 7-Band Voice Equalizer */
              <div className="flex items-center gap-1">
                {speechWave.map((h, i) => (
                  <span
                    key={i}
                    className="w-1 rounded-full transition-all duration-100"
                    style={{
                      height: `${Math.max(3, Math.round(h * 0.45))}px`,
                      backgroundColor: currentConfig.accentColor,
                      boxShadow: `0 0 6px ${currentConfig.glowColor}`,
                    }}
                  />
                ))}
              </div>
            ) : mascotState === 'listening' ? (
              /* Reactive Voice Ingestion Waveform */
              <div className="flex items-center gap-1.5">
                <span
                  className="w-1.5 h-1.5 rounded-full animate-ping"
                  style={{ backgroundColor: currentConfig.accentColor }}
                />
                <span
                  className="w-12 h-1 rounded-full"
                  style={{
                    backgroundColor: currentConfig.accentColor,
                    boxShadow: `0 0 8px ${currentConfig.glowColor}`,
                  }}
                />
                <span
                  className="w-1.5 h-1.5 rounded-full animate-ping"
                  style={{ backgroundColor: currentConfig.accentColor }}
                />
              </div>
            ) : mascotState === 'thinking' ? (
              /* Cascading Neural Progress Dots */
              <div className="flex items-center gap-1.5">
                <span
                  className="w-1.5 h-1.5 rounded-full animate-bounce"
                  style={{ backgroundColor: currentConfig.accentColor }}
                />
                <span
                  className="w-1.5 h-1.5 rounded-full animate-bounce [animation-delay:150ms]"
                  style={{ backgroundColor: currentConfig.accentColor }}
                />
                <span
                  className="w-1.5 h-1.5 rounded-full animate-bounce [animation-delay:300ms]"
                  style={{ backgroundColor: currentConfig.accentColor }}
                />
              </div>
            ) : mascotState === 'success' ? (
              /* Warm Upturned Smile Curve */
              <div
                className="w-8 h-2 rounded-b-full border-b-2 bg-transparent"
                style={{
                  borderColor: currentConfig.accentColor,
                  filter: `drop-shadow(0 0 6px ${currentConfig.glowColor})`,
                }}
              />
            ) : (
              /* Calm Resting Horizon */
              <div
                className="w-6 h-0.5 rounded-full transition-all duration-300"
                style={{
                  backgroundColor: currentConfig.accentColor,
                  opacity: 0.5,
                }}
              />
            )}
          </div>
        </div>
      </div>

      {/* Dynamic Counter-Phase Ambient Floor Illumination */}
      <div
        className="rounded-full blur-md mt-3 transition-all duration-300 opacity-60"
        style={{
          width: compact ? '9rem' : '13rem',
          height: '0.65rem',
          backgroundColor: currentConfig.glowColor,
        }}
      />
    </div>
  );

  // 1. Compact Header Mode (Used when embedded in compact toolbars)
  if (isCompact) {
    return (
      <section
        className="flex flex-col items-center justify-center relative select-none bg-gradient-to-b from-bg-card/40 via-bg-card/20 to-bg-main border-b border-border-subtle shrink-0 z-10 pt-2.5 pb-2 px-4"
        aria-label="Kai Vector Mascot Companion Stage"
      >
        <div className="w-full flex items-center justify-between px-2 mb-1.5 text-xs font-mono">
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border border-border-subtle bg-bg-card text-[11px] text-text-secondary shadow-xs">
            <span
              className="w-1.5 h-1.5 rounded-full animate-pulse"
              style={{ backgroundColor: currentConfig.accentColor }}
            />
            <span
              className="font-medium tracking-wide"
              style={{ color: currentConfig.accentColor }}
            >
              {currentConfig.label}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <h2 className="text-xs font-semibold tracking-tight text-text-primary">
              Kai Vector Mascot
            </h2>
            <span className="text-[10px] font-mono text-text-muted px-1.5 py-0.5 rounded border border-border-subtle bg-bg-card-subtle">
              PERSONAL COMPANION
            </span>
          </div>
        </div>

        {renderMascotGraphic(true)}
      </section>
    );
  }

  // 2. Main Executive Center Companion Stage
  return (
    <section
      className="flex-1 flex flex-col items-center justify-center p-6 select-none relative overflow-y-auto bg-gradient-to-b from-bg-card/20 via-bg-main to-bg-main"
      aria-label="Kai Vector Mascot Companion Stage"
    >
      {/* Ambient Radial Illumination Glow (Color matched to state) */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[540px] h-[360px] blur-[130px] rounded-full pointer-events-none transition-all duration-500 opacity-20"
        style={{ backgroundColor: currentConfig.accentColor }}
      />

      {/* Unified Executive Pedestal Deck */}
      <div className="w-full max-w-2xl flex flex-col gap-4 relative z-10 my-auto">
        {/* Top Header Bar */}
        <div className="w-full flex items-center justify-between px-1 text-xs font-mono">
          {/* Mascot Identity */}
          <div className="flex items-center gap-2">
            <h2 className="text-xs font-bold tracking-tight text-text-primary">
              Kai Vector Mascot
            </h2>
            <span className="text-[10px] font-mono text-text-muted px-2 py-0.5 rounded-full border border-border-subtle bg-bg-card-subtle">
              PERSONAL COMPANION
            </span>
          </div>

          {/* Status Beacon */}
          <div className="flex items-center gap-2 px-3 py-1 rounded-full border border-border-subtle bg-bg-card text-[11px] text-text-secondary shadow-xs">
            <span className="relative flex h-2 w-2">
              <span
                className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
                style={{ backgroundColor: currentConfig.accentColor }}
              />
              <span
                className="relative inline-flex rounded-full h-2 w-2"
                style={{ backgroundColor: currentConfig.accentColor }}
              />
            </span>
            <span
              className="font-semibold tracking-wide"
              style={{ color: currentConfig.accentColor }}
            >
              {currentConfig.label}
            </span>
          </div>
        </div>

        {/* Hero Mascot Pedestal Card */}
        <div className="w-full rounded-3xl border border-border-subtle bg-bg-card/50 backdrop-blur-xl p-8 flex flex-col items-center justify-center relative shadow-2xl overflow-hidden group">
          {/* Subtle Top Metallic Highlight Bevel */}
          <div className="absolute top-0 inset-x-12 h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent" />

          {/* Centered Floating Mascot */}
          {renderMascotGraphic(false)}

          {/* Voice Intercom Action & Companion Telemetry (Non-chat design) */}
          <div className="mt-5 flex flex-col items-center gap-2.5 z-10">
            {/* Dedicated Voice Intercom Button */}
            <button
              type="button"
              onClick={toggleIntercom}
              className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full border transition-all cursor-pointer font-mono text-xs shadow-xs active:scale-95 ${
                mascotState === 'listening'
                  ? 'bg-red-500/20 text-red-400 border-red-500/50 shadow-[0_0_16px_rgba(239,68,68,0.3)] animate-pulse font-medium'
                  : 'border-border-subtle bg-bg-card hover:bg-bg-card-hover text-text-secondary hover:text-text-primary hover:border-accent/40'
              }`}
              title={mascotState === 'listening' ? 'Mute Microphone' : 'Engage Voice Intercom'}
            >
              {mascotState === 'listening' ? (
                <>
                  <MicOff className="w-3.5 h-3.5 text-red-400" />
                  <span>Listening... Click to stop</span>
                </>
              ) : (
                <>
                  <Mic className="w-3.5 h-3.5 text-accent" />
                  <span>Voice Intercom</span>
                </>
              )}
            </button>

            {/* Ambient Telemetry Status Caption (Plain text line, zero input appearance) */}
            <div className="flex items-center gap-2 text-[11px] font-mono text-text-muted">
              <StateIcon
                className="w-3 h-3 shrink-0 animate-pulse"
                style={{ color: currentConfig.accentColor }}
              />
              <span className="truncate max-w-[360px]">
                {activeMessage}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

