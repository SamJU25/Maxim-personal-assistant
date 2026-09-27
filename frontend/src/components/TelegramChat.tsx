import React, { useState, useRef, useEffect, useMemo } from 'react';
import {
  Send,
  Paperclip,
  Plus,
  ChevronDown,
  ChevronUp,
  Brain,
  FileText,
  Image as ImageIcon,
  X,
  Zap,
  Maximize2,
  ExternalLink,
  MessageSquare,
  Check,
  RefreshCw,
  Folder,
  Volume2,
  Square,
} from 'lucide-react';
import { ChatMessage, ChatAttachment, DocumentItem, ChatSession } from '../types';

interface LocalModelInfo {
  id: string;
  repo_id: string;
  name: string;
  file_name: string;
  path: string;
  size_gb: number;
  quant: string;
  category: string;
  category_name?: string;
  category_icon?: string;
  role_description?: string;
  subfolder?: string;
  is_project_local?: boolean;
  location?: string;
  source?: string;
}

interface ConnectedCloudProvider {
  provider: string;
  name: string;
  model_name: string;
  base_url: string;
  is_cloud: boolean;
}

export interface TelegramChatProps {
  onSendMessage?: (content: string, model: string, attachments: ChatAttachment[]) => void;
  initialMessages?: ChatMessage[];
  initialSessions?: ChatSession[];
}

export const TelegramChat: React.FC<TelegramChatProps> = ({
  onSendMessage,
  initialMessages = [],
  initialSessions = [
    { id: '1', title: 'Main Workspace', updatedAt: 'Just now', messageCount: 0 },
  ],
}) => {
  const [sessions, setSessions] = useState<ChatSession[]>(initialSessions);
  const [activeSessionId, setActiveSessionId] = useState<string>('1');
  const [isSessionMenuOpen, setIsSessionMenuOpen] = useState<boolean>(false);

  const [selectedModel, setSelectedModel] = useState<string>('local:auto');
  const [isModelMenuOpen, setIsModelMenuOpen] = useState<boolean>(false);
  const modelMenuRef = useRef<HTMLDivElement | null>(null);

  const [localModels, setLocalModels] = useState<LocalModelInfo[]>([]);
  const [connectedCloudProviders, setConnectedCloudProviders] = useState<ConnectedCloudProvider[]>([]);
  const [isScanningModels, setIsScanningModels] = useState<boolean>(false);

  const fetchModels = async () => {
    try {
      setIsScanningModels(true);
      const [localRes, provRes] = await Promise.all([
        fetch('/api/local/models').catch(() => null),
        fetch('/api/providers').catch(() => null),
      ]);
      if (localRes && localRes.ok) {
        const data = await localRes.json();
        if (Array.isArray(data.models)) {
          setLocalModels(data.models);
        }
      }
      if (provRes && provRes.ok) {
        const pData = await provRes.json();
        if (Array.isArray(pData.connected_cloud_providers)) {
          setConnectedCloudProviders(pData.connected_cloud_providers);
        } else if (pData.providers) {
          const localNames = new Set(['local', 'unsloth', 'ollama', 'custom', 'chatgpt']);
          const list: ConnectedCloudProvider[] = [];
          for (const [key, p] of Object.entries<any>(pData.providers)) {
            if (!localNames.has(key.toLowerCase()) && p.configured) {
              list.push({
                provider: key,
                name: p.name || key,
                model_name: p.model_name || 'default',
                base_url: p.base_url || '',
                is_cloud: true,
              });
            }
          }
          setConnectedCloudProviders(list);
        }
      }
    } catch (err) {
      console.error('Failed to scan models:', err);
    } finally {
      setIsScanningModels(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const categorizedModelGroups = useMemo(() => {
    const autoOption = {
      value: 'local:auto',
      label: '⚡ Auto-Select (Laya Adaptive Routing)',
      badge: 'Laya System 1',
      category: 'auto',
      description: 'Laya evaluates task capabilities across Local & Online models with autonomous browsing',
    };

    const llmModels = localModels
      .filter((m) => m.category === 'llm')
      .map((m) => ({
        value: `local:${m.id}`,
        label: `${m.is_project_local ? '📁' : '🖥️'} ${m.name} (${m.quant}, ${m.size_gb}GB)`,
        badge: m.subfolder || 'models/llm',
        category: 'llm',
        description: m.role_description,
      }));

    const visionModels = localModels
      .filter((m) => m.category === 'vision')
      .map((m) => ({
        value: `local:${m.id}`,
        label: `👁️ ${m.name} (${m.quant}, ${m.size_gb}GB)`,
        badge: m.subfolder || 'models/vision',
        category: 'vision',
        description: m.role_description || 'Multimodal Vision Model (Qwen3VL + mmproj)',
      }));

    // Dynamic Connected Cloud Models: Only show cloud providers that are verified and configured
    const cloudModels = connectedCloudProviders.map((cp) => ({
      value: `cloud:${cp.provider}:${cp.model_name}`,
      label: `☁️ ${cp.name} (${cp.model_name})`,
      badge: 'Cloud Connected',
      category: 'cloud',
      description: `Direct inference via ${cp.name} API (${cp.model_name})`,
    }));

    return {
      auto: [autoOption],
      llm: llmModels,
      vision: visionModels,
      cloud: cloudModels,
    };
  }, [localModels, connectedCloudProviders]);

  const modelOptions = useMemo(() => {
    return [
      ...categorizedModelGroups.auto,
      ...categorizedModelGroups.llm,
      ...categorizedModelGroups.vision,
      ...categorizedModelGroups.cloud,
    ];
  }, [categorizedModelGroups]);

  // Audio playback & Voice synthesis state
  const [isPlayingAudio, setIsPlayingAudio] = useState<string | null>(null);
  const [isAutoSpeak] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem('maxim_auto_speak');
      return saved !== null ? saved === 'true' : false;
    } catch {
      return false;
    }
  });
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioQueueRef = useRef<HTMLAudioElement[]>([]);
  const isAudioQueuePlayingRef = useRef<boolean>(false);

  const stopAllAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    audioQueueRef.current.forEach((a) => {
      try {
        a.pause();
      } catch {}
    });
    audioQueueRef.current = [];
    isAudioQueuePlayingRef.current = false;
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsPlayingAudio(null);
  };

  useEffect(() => {
    return () => {
      stopAllAudio();
    };
  }, []);

  const cleanTextForSpeech = (text: string): string => {
    return text
      .replace(/```[\s\S]*?```/g, '')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/[#*_~>]/g, '')
      .trim();
  };

  const playStudioAudioQueue = () => {
    if (isAudioQueuePlayingRef.current || audioQueueRef.current.length === 0) return;
    isAudioQueuePlayingRef.current = true;
    const nextAudio = audioQueueRef.current.shift();
    if (!nextAudio) {
      isAudioQueuePlayingRef.current = false;
      return;
    }
    audioRef.current = nextAudio;
    nextAudio.onended = () => {
      isAudioQueuePlayingRef.current = false;
      if (audioQueueRef.current.length > 0) {
        playStudioAudioQueue();
      } else {
        setIsPlayingAudio(null);
        window.dispatchEvent(
          new CustomEvent('maxim:mascot-state', {
            detail: { state: 'idle', message: 'Neural loop online • Standing by for voice or text' },
          })
        );
      }
    };
    nextAudio.onerror = () => {
      isAudioQueuePlayingRef.current = false;
      if (audioQueueRef.current.length > 0) {
        playStudioAudioQueue();
      } else {
        setIsPlayingAudio(null);
      }
    };
    nextAudio.play().catch(() => {
      isAudioQueuePlayingRef.current = false;
      playStudioAudioQueue();
    });
  };

  const speakSentenceChunk = async (sentence: string, msgId: string, isFirst: boolean = false) => {
    const cleaned = cleanTextForSpeech(sentence);
    if (!cleaned) return;

    const voiceMode = (() => {
      try {
        return (localStorage.getItem('maxim_voice_mode') as 'turbo' | 'studio') || 'turbo';
      } catch {
        return 'turbo';
      }
    })();

    setIsPlayingAudio(msgId);
    window.dispatchEvent(
      new CustomEvent('maxim:mascot-state', {
        detail: {
          state: 'talking',
          message: voiceMode === 'turbo' ? 'Speaking response out loud (Turbo)...' : 'Speaking response out loud (Studio)...',
        },
      })
    );

    if (voiceMode === 'turbo' && 'speechSynthesis' in window) {
      if (isFirst) {
        window.speechSynthesis.cancel();
      }
      const utterance = new SpeechSynthesisUtterance(cleaned.slice(0, 1000));
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice =
        voices.find(
          (v) =>
            v.lang.startsWith('en') &&
            (v.name.includes('Natural') ||
              v.name.includes('Neural') ||
              v.name.includes('David') ||
              v.name.includes('Mark') ||
              v.name.includes('Guy') ||
              v.name.includes('George'))
        ) || voices.find((v) => v.lang.startsWith('en'));

      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }
      utterance.rate = 1.05;

      utterance.onend = () => {
        setTimeout(() => {
          if (!window.speechSynthesis.speaking) {
            setIsPlayingAudio(null);
            window.dispatchEvent(
              new CustomEvent('maxim:mascot-state', {
                detail: { state: 'idle', message: 'Neural loop online • Standing by for voice or text' },
              })
            );
          }
        }, 120);
      };

      utterance.onerror = () => {
        setTimeout(() => {
          if (!window.speechSynthesis.speaking) {
            setIsPlayingAudio(null);
          }
        }, 120);
      };

      window.speechSynthesis.speak(utterance);
      return;
    }

    // Studio Neural Mode: Synthesize sentence chunk and append to queue
    try {
      const res = await fetch('/api/voice/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: cleaned.slice(0, 1000),
          engine: 'edge',
        }),
      });
      if (res.ok) {
        const blob = await res.blob();
        const audioUrl = URL.createObjectURL(blob);
        const audio = new Audio(audioUrl);
        audioQueueRef.current.push(audio);
        playStudioAudioQueue();
      }
    } catch (e) {
      console.warn('Studio voice chunk synthesis error:', e);
    }
  };

  const playVoice = async (text: string, msgId: string) => {
    if (isPlayingAudio === msgId) {
      stopAllAudio();
      return;
    }

    stopAllAudio();

    const cleanedText = cleanTextForSpeech(text);
    if (!cleanedText) return;

    speakSentenceChunk(cleanedText, msgId, true);
  };

  const [inputMessage, setInputMessage] = useState<string>('');
  const [attachments, setAttachments] = useState<ChatAttachment[]>([]);
  const [expandedThinking, setExpandedThinking] = useState<Record<string, boolean>>({});

  // Lightbox & Document Reader Modals
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<DocumentItem | null>(null);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Chat messages state (clean initial state, receives real messages on query)
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);

  const isInitialMount = useRef(true);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }
    scrollToBottom();
  }, [messages]);

  // Click-outside listener for model combobox menu
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modelMenuRef.current && !modelMenuRef.current.contains(event.target as Node)) {
        setIsModelMenuOpen(false);
      }
    };
    if (isModelMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isModelMenuOpen]);

  // Listen for perception feed frame captures (from VisualUplink camera / screen share)
  useEffect(() => {
    const handleAttachPerceptionFrame = (e: Event) => {
      const customEvent = e as CustomEvent<{ dataUrl: string; source: string; timestamp?: string }>;
      const { dataUrl, source } = customEvent.detail || {};
      if (!dataUrl) return;

      const sourceLabel = source === 'screen' ? 'Screen Share' : 'Camera Feed';
      const filename = `perception_${source || 'frame'}_${Date.now()}.jpg`;
      const sizeBytes = Math.round((dataUrl.length * 3) / 4);

      setAttachments((prev) => [
        ...prev,
        {
          name: filename,
          sizeBytes,
          type: 'image/jpeg',
          dataUrl,
        },
      ]);

      // If user hasn't typed an input message yet, provide an intuitive prompt
      setInputMessage((prev) => {
        if (!prev.trim()) {
          return `Analyze this ${sourceLabel.toLowerCase()} frame. What do you see?`;
        }
        return prev;
      });
    };

    window.addEventListener('maxim:attach-perception-frame', handleAttachPerceptionFrame);
    return () => {
      window.removeEventListener('maxim:attach-perception-frame', handleAttachPerceptionFrame);
    };
  }, []);

  const toggleThinking = (msgId: string) => {
    setExpandedThinking((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    Array.from(files).forEach((file) => {
      const isImg = file.type.startsWith('image/');
      const reader = new FileReader();

      reader.onload = () => {
        setAttachments((prev) => [
          ...prev,
          {
            name: file.name,
            sizeBytes: file.size,
            type: file.type,
            dataUrl: isImg ? (reader.result as string) : undefined,
            content: !isImg ? (reader.result as string) : undefined,
          },
        ]);
      };

      if (isImg) {
        reader.readAsDataURL(file);
      } else {
        reader.readAsText(file);
      }
    });

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  };

  const executeSend = async (
    text: string,
    currentAttachments: ChatAttachment[] = attachments,
    forceVoiceResponse: boolean = false
  ) => {
    if (!text.trim() && currentAttachments.length === 0) return;
    stopAllAudio();

    const newMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }),
      attachments: currentAttachments.length > 0 ? [...currentAttachments] : undefined,
    };

    setMessages((prev) => [...prev, newMsg]);
    setInputMessage('');
    setAttachments([]);
    onSendMessage?.(text, selectedModel, currentAttachments);

    const hasImage = currentAttachments.some(
      (a) => a.type?.startsWith('image/') || /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(a.name)
    );
    const isImageIntent =
      hasImage ||
      /image|picture|photo|screenshot|chart|diagram|ocr|visual|look at this|draw|view image|see an image|see image|find image|generating image|generate image/i.test(
        text
      );
    const isSearchTask = !isImageIntent && /search|vault|note|find|query|graph|doc|read/i.test(text);

    // Phase 1: Ingestion & Perception/Reasoning
    window.dispatchEvent(
      new CustomEvent('maxim:mascot-state', {
        detail: {
          state: isSearchTask ? 'searching' : 'thinking',
          message: isImageIntent
            ? 'Activating Vision & Multimodal neural pipeline...'
            : isSearchTask
            ? 'Scanning Obsidian vault & knowledge graph...'
            : `Evaluating directive with ${selectedModel}...`,
        },
      })
    );

    // Prepare assistant streaming placeholder
    const assistantMsgId = `resp-${Date.now()}`;
    const initialAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      sender: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }),
      thinking: '',
    };
    setMessages((prev) => [...prev, initialAssistantMsg]);

    let providerPart = 'local';
    let modelPart = selectedModel;
    if (selectedModel.startsWith('cloud:')) {
      const parts = selectedModel.split(':');
      providerPart = parts[1];
      modelPart = parts[2] || '';
    } else if (selectedModel.startsWith('local:')) {
      providerPart = 'local';
      modelPart = selectedModel.slice(6);
    } else {
      const firstColon = selectedModel.indexOf(':');
      providerPart = firstColon !== -1 ? selectedModel.slice(0, firstColon) : 'local';
      modelPart = firstColon !== -1 ? selectedModel.slice(firstColon + 1) : selectedModel;
    }

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          session_id: activeSessionId,
          stream: true,
          provider: providerPart,
          model: modelPart,
          has_image: hasImage,
          attachments: currentAttachments.map((a) => ({
            name: a.name,
            type: a.type,
            sizeBytes: a.sizeBytes,
            dataUrl: a.dataUrl,
            content: a.content,
          })),
        }),
      });

      if (!response.ok || !response.body) {
        const errText = await response.text();
        throw new Error(errText || `Server returned HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let accumulatedContent = '';
      let accumulatedThinking = '';
      let accumulatedImages: string[] = [];
      let spokenCharIndex = 0;
      let isFirstSentenceSpoken = true;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data:')) continue;
          const jsonStr = trimmed.slice(5).trim();
          if (!jsonStr) continue;

          try {
            const event = JSON.parse(jsonStr);

            if (event.type === 'status') {
              window.dispatchEvent(
                new CustomEvent('maxim:mascot-state', {
                  detail: { state: 'thinking', message: event.message },
                })
              );
              accumulatedThinking += (accumulatedThinking ? '\n' : '') + `[Status] ${event.message}`;
            } else if (event.type === 'image') {
              const imgUrl = event.url;
              if (imgUrl && !accumulatedImages.includes(imgUrl)) {
                accumulatedImages.push(imgUrl);
              }
            } else if (event.type === 'tool_call') {
              const isVault = /vault|note|read|search/i.test(event.tool);
              window.dispatchEvent(
                new CustomEvent('maxim:mascot-state', {
                  detail: {
                    state: isVault ? 'searching' : 'executing',
                    message: `Executing ${event.tool}...`,
                  },
                })
              );
              accumulatedThinking += (accumulatedThinking ? '\n' : '') + `[Tool Call] ${event.tool}(${JSON.stringify(event.args || {})})`;
            } else if (event.type === 'tool_result') {
              const summary = typeof event.output === 'string' ? event.output : JSON.stringify(event.output);
              accumulatedThinking += (accumulatedThinking ? '\n' : '') + `[Tool Result] ${event.tool}: ${summary.slice(0, 160)}`;
              if (event.tool === 'generate_image') {
                try {
                  const parsed = typeof event.output === 'string' ? JSON.parse(event.output) : event.output;
                  const imgUrl = parsed?.image_url || parsed?.direct_url;
                  if (imgUrl && !accumulatedImages.includes(imgUrl)) {
                    accumulatedImages.push(imgUrl);
                  }
                } catch {
                  // ignore
                }
              }
            } else if (event.type === 'content') {
              accumulatedContent += event.content;
              window.dispatchEvent(
                new CustomEvent('maxim:mascot-state', {
                  detail: { state: 'talking', message: 'Synthesizing response & vocal articulation...' },
                })
              );

              // Low-Latency Vocal Articulation: Stream sentence-by-sentence to voice engine immediately
              if (isAutoSpeak || forceVoiceResponse) {
                const unvocalized = accumulatedContent.slice(spokenCharIndex);
                // Look for sentence terminators (. ? !) followed by whitespace, newline, or end of clause
                const match = unvocalized.search(/[.?!](\s|\n|$)/);
                if (match !== -1 && match >= 2) {
                  const sentenceCandidate = unvocalized.slice(0, match + 1).trim();
                  if (!/\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|e\.g|i\.e)\.$/i.test(sentenceCandidate)) {
                    spokenCharIndex += match + 1;
                    speakSentenceChunk(sentenceCandidate, assistantMsgId, isFirstSentenceSpoken);
                    isFirstSentenceSpoken = false;
                  }
                }
              }
            } else if (event.type === 'done') {
              window.dispatchEvent(
                new CustomEvent('maxim:mascot-state', {
                  detail: { state: 'success', message: 'Directive verified and receipts recorded.' },
                })
              );
              // MaxIM speaks remaining unvocalized text if Auto-Speak is enabled OR if query was initiated via Voice Intercom
              if (isAutoSpeak || forceVoiceResponse) {
                const tailChunk = accumulatedContent.slice(spokenCharIndex).trim();
                if (tailChunk) {
                  speakSentenceChunk(tailChunk, assistantMsgId, isFirstSentenceSpoken);
                } else if (isFirstSentenceSpoken && accumulatedContent.trim()) {
                  speakSentenceChunk(accumulatedContent, assistantMsgId, true);
                }
              } else {
                setTimeout(() => {
                  window.dispatchEvent(
                    new CustomEvent('maxim:mascot-state', {
                      detail: { state: 'idle', message: 'Neural loop online • Standing by for voice or text' },
                    })
                  );
                }, 2200);
              }
            } else if (event.type === 'error') {
              accumulatedContent += (accumulatedContent ? '\n\n' : '') + `⚠️ **Subsystem Alert:** ${event.error}`;
              window.dispatchEvent(
                new CustomEvent('maxim:mascot-state', {
                  detail: { state: 'alert', message: event.error },
                })
              );
            }

            // Extract any markdown image tags: ![...](/api/images/...) or ![...](https://...)
            const mdMatches = Array.from(accumulatedContent.matchAll(/!\[.*?\]\(((?:\/api\/images\/|https?:\/\/)[^\s)]+)\)/g));
            for (const m of mdMatches) {
              if (m[1] && !accumulatedImages.includes(m[1])) {
                accumulatedImages.push(m[1]);
              }
            }

            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? {
                      ...msg,
                      content: accumulatedContent || (accumulatedThinking ? 'Analyzing directives...' : ''),
                      thinking: accumulatedThinking || undefined,
                      imageUrls: accumulatedImages.length > 0 ? [...accumulatedImages] : undefined,
                    }
                  : msg
              )
            );
          } catch (parseErr) {
            console.error('SSE parse error:', parseErr);
          }
        }
      }
    } catch (err: any) {
      console.error('Chat execution failed:', err);
      const errMsg = err?.message || 'Failed to connect to backend';
      const displayErr = errMsg.includes('Failed to fetch') || errMsg.includes('NetworkError')
        ? '⚠️ **Connection Error:** Backend at http://127.0.0.1:8000 is unreachable. Please verify server status.'
        : `⚠️ **Execution Error:** ${errMsg}`;

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                content: displayErr,
                thinking: `Connection attempt to /api/chat failed.\nDetails: ${errMsg}`,
              }
            : msg
        )
      );

      window.dispatchEvent(
        new CustomEvent('maxim:mascot-state', {
          detail: { state: 'alert', message: 'Connection to cognitive engine interrupted.' },
        })
      );
      setTimeout(() => {
        window.dispatchEvent(
          new CustomEvent('maxim:mascot-state', {
            detail: { state: 'idle', message: 'Neural loop online • Standing by for voice or text' },
          })
        );
      }, 3000);
    }
  };

  const handleSend = () => {
    executeSend(inputMessage);
  };

  // Listen for externally dispatched prompts (e.g. from Daily Directives or Voice Intercom)
  useEffect(() => {
    const handlePromptEvent = (e: Event) => {
      const detail = (e as CustomEvent<{ prompt: string; source?: string }>).detail;
      if (detail?.prompt) {
        executeSend(detail.prompt, [], detail.source === 'voice');
      }
    };
    const handleStopAudio = () => {
      stopAllAudio();
    };
    window.addEventListener('maxim:send-prompt', handlePromptEvent);
    window.addEventListener('maxim:stop-speaking', handleStopAudio);
    return () => {
      window.removeEventListener('maxim:send-prompt', handlePromptEvent);
      window.removeEventListener('maxim:stop-speaking', handleStopAudio);
    };
  }, [selectedModel]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewChat = () => {
    const newSessionId = String(Date.now());
    const newSession: ChatSession = {
      id: newSessionId,
      title: `Conversation ${sessions.length + 1}`,
      updatedAt: 'Just now',
      messageCount: 0,
    };
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newSessionId);
    setMessages([]);
  };

  const activeSessionTitle =
    sessions.find((s) => s.id === activeSessionId)?.title || 'Main Workspace';

  const currentModelDisplayLabel = useMemo(() => {
    if (selectedModel === 'local:auto') return '🤖 Auto-Select';
    const found = modelOptions.find((m) => m.value === selectedModel);
    if (!found) return selectedModel;
    return found.label.replace(/\s*\(Smart Multi-Model Routing\)/i, '');
  }, [selectedModel, modelOptions]);

  return (
    <section className="flex-1 min-h-0 flex flex-col select-none relative overflow-hidden bg-bg-main">
      {/* 1. Compact Session Switcher Header */}
      <div className="h-9 border-b border-border-subtle px-3 flex items-center justify-between text-xs bg-bg-card/40 backdrop-blur-md z-20 shrink-0">
        <div className="relative">
          <button
            onClick={() => setIsSessionMenuOpen(!isSessionMenuOpen)}
            className="flex items-center gap-1.5 font-medium text-text-primary hover:text-accent transition-colors group cursor-pointer"
          >
            <span className="line-clamp-1 max-w-[170px] text-[11px]">{activeSessionTitle}</span>
            <ChevronDown className="w-3 h-3 text-text-muted group-hover:text-text-primary transition-transform" />
          </button>

          {/* Session Switcher Dropdown */}
          {isSessionMenuOpen && (
            <div className="absolute top-7 left-0 w-64 rounded-md border border-border-subtle bg-bg-card p-1.5 shadow-xl z-50 flex flex-col gap-1 animate-in fade-in duration-100">
              <div className="text-[10px] font-mono text-text-muted px-2 py-1 uppercase tracking-wider">
                Previous Chats
              </div>
              {sessions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => {
                    setActiveSessionId(s.id);
                    setIsSessionMenuOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-sm text-xs transition-colors text-left cursor-pointer ${
                    activeSessionId === s.id
                      ? 'bg-accent text-accent-contrast font-medium'
                      : 'text-text-secondary hover:text-text-primary hover:bg-bg-card-hover'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <MessageSquare className="w-3 h-3" />
                    <span className="truncate max-w-[130px]">{s.title}</span>
                  </div>
                  <span className="text-[10px] font-mono opacity-60">{s.updatedAt}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={handleNewChat}
          className="flex items-center gap-1 px-2 py-0.5 rounded border border-border-subtle bg-bg-card hover:bg-bg-card-hover text-text-secondary hover:text-text-primary font-mono text-[10px] transition-all active:scale-95 shadow-xs cursor-pointer"
          title="Create New Conversation"
        >
          <Plus className="w-3 h-3" />
          <span>New Chat</span>
        </button>
      </div>

      {/* 2. Message Stream (Telegram Bubbles) */}
      <div className="flex-1 min-h-0 p-4 overflow-y-auto flex flex-col gap-3.5 scroll-smooth">
        {/* Message Bubble Stream */}
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          return (
            <div
              key={msg.id}
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-full`}
            >
              {/* Agent Thinking Accordion Drawer */}
              {!isUser && msg.thinking && (
                <div className="mb-1.5 max-w-[90%]">
                  <button
                    onClick={() => toggleThinking(msg.id)}
                    className="flex items-center gap-1.5 text-[10px] font-mono px-2 py-0.5 rounded-full border border-border-subtle bg-bg-card text-text-muted hover:text-text-primary transition-colors"
                  >
                    <Brain className="w-3 h-3 text-text-secondary" />
                    <span>Thought Process</span>
                    {expandedThinking[msg.id] ? (
                      <ChevronUp className="w-3 h-3" />
                    ) : (
                      <ChevronDown className="w-3 h-3" />
                    )}
                  </button>

                  {expandedThinking[msg.id] && (
                    <div className="mt-1 p-2 rounded-lg border border-border-subtle bg-bg-card-subtle text-[11px] font-mono text-text-secondary leading-relaxed animate-in fade-in duration-100">
                      {msg.thinking}
                    </div>
                  )}
                </div>
              )}

              {/* Message Bubble Body */}
              <div
                className={`rounded-md p-3 text-xs leading-relaxed max-w-[88%] shadow-xs ${
                  isUser
                    ? 'bg-accent text-accent-contrast font-sans'
                    : 'bg-bg-card border border-border-subtle text-text-primary font-sans'
                }`}
              >
                {/* Text Content */}
                <p className="whitespace-pre-wrap">{msg.content}</p>

                {/* Attached Files inside user message */}
                {msg.attachments && msg.attachments.length > 0 && (
                  <div className="mt-2 flex flex-col gap-1">
                    {msg.attachments.map((att, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-1.5 text-[11px] font-mono p-1.5 rounded bg-black/10 dark:bg-white/10"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span className="truncate max-w-[180px]">{att.name}</span>
                        <span className="opacity-60 text-[10px]">
                          ({Math.round(att.sizeBytes / 1024)}KB)
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Attached Document Card (Assistant) */}
                {msg.documents && msg.documents.length > 0 && (
                  <div className="mt-2.5 flex flex-col gap-1.5">
                    {msg.documents.map((doc) => (
                      <div
                        key={doc.id}
                        onClick={() => setSelectedDocument(doc)}
                        className="flex items-center justify-between p-2 rounded-md border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover cursor-pointer transition-all group"
                      >
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-text-secondary group-hover:text-text-primary" />
                          <div className="flex flex-col">
                            <span className="text-[11px] font-semibold text-text-primary group-hover:underline">
                              {doc.title}
                            </span>
                            <span className="text-[10px] text-text-muted font-mono">
                              {doc.category}
                            </span>
                          </div>
                        </div>
                        <ExternalLink className="w-3 h-3 text-text-muted group-hover:text-text-primary" />
                      </div>
                    ))}
                  </div>
                )}

                {/* Generated Image Previews (Assistant) */}
                {msg.imageUrls && msg.imageUrls.length > 0 && (
                  <div className="mt-2.5 flex flex-wrap gap-2">
                    {msg.imageUrls.map((url, i) => (
                      <div
                        key={i}
                        onClick={() => setSelectedImage(url)}
                        className="relative rounded-xl overflow-hidden border border-border-subtle cursor-pointer group w-64 h-36 bg-black/40 shadow-xs"
                      >
                        <img
                          src={url}
                          alt="AI Generated Output"
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                        <div className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                          <span className="text-[11px] font-mono text-white flex items-center gap-1 bg-black/70 px-2 py-1 rounded-md">
                            <Maximize2 className="w-3 h-3" /> View Image
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Timestamp & Voice Playback Footer */}
                <div
                  className={`flex items-center justify-between mt-1 text-[10px] font-mono ${
                    isUser ? 'opacity-70 justify-end' : 'text-text-muted'
                  }`}
                >
                  {!isUser && msg.content && (
                    <button
                      type="button"
                      onClick={() => playVoice(msg.content, msg.id)}
                      className={`flex items-center gap-1 px-1.5 py-0.5 rounded cursor-pointer transition-colors ${
                        isPlayingAudio === msg.id
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : 'hover:text-accent hover:bg-bg-card-subtle'
                      }`}
                      title={isPlayingAudio === msg.id ? 'Stop speaking' : 'Read aloud with Neural Voice'}
                    >
                      {isPlayingAudio === msg.id ? (
                        <>
                          <Square className="w-2.5 h-2.5 fill-current animate-pulse text-rose-400" />
                          <span className="font-semibold text-rose-400">Speaking...</span>
                        </>
                      ) : (
                        <>
                          <Volume2 className="w-2.5 h-2.5" />
                          <span>Speak</span>
                        </>
                      )}
                    </button>
                  )}
                  <span>{msg.timestamp}</span>
                </div>
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* 3. Telegram-Inspired Input Dock */}
      <div className="p-3 border-t border-border-subtle bg-bg-card flex flex-col gap-2 z-20">
        {/* Model Selector Drop-up Combobox (Opens Upward) */}
        <div className="flex items-center text-[11px] font-mono text-text-muted px-1">
          <div className="relative flex items-center gap-1.5 min-w-0" ref={modelMenuRef}>
            <Zap className="w-3 h-3 text-text-secondary shrink-0" />
            <span className="shrink-0 text-text-secondary font-medium">Model:</span>

            {/* Combobox Trigger */}
            <button
              type="button"
              role="combobox"
              aria-expanded={isModelMenuOpen}
              aria-haspopup="listbox"
              onClick={() => setIsModelMenuOpen((prev) => !prev)}
              className="h-6 max-w-[200px] bg-bg-card-subtle border border-border-subtle hover:border-accent/40 text-text-primary rounded px-2 outline-none cursor-pointer text-[11px] font-mono inline-flex items-center justify-between gap-1.5 transition-all shadow-xs shrink-0 select-none"
              title={modelOptions.find((m) => m.value === selectedModel)?.label || selectedModel}
            >
              <span className="truncate whitespace-nowrap">{currentModelDisplayLabel}</span>
              <ChevronUp className={`w-3 h-3 shrink-0 text-text-muted transition-transform duration-150 ${isModelMenuOpen ? 'rotate-180 text-accent' : ''}`} />
            </button>

            {/* Pop-up Listbox Options (Opens UPWARDS above the combobox trigger) */}
            {isModelMenuOpen && (
              <div
                role="listbox"
                className="absolute bottom-full mb-1.5 left-0 w-80 max-h-96 overflow-y-auto rounded-xl border border-border-subtle bg-bg-card p-1.5 shadow-2xl z-50 flex flex-col gap-1.5 animate-in fade-in duration-100 backdrop-blur-md"
              >
                <div className="flex items-center justify-between text-[10px] font-mono text-text-muted px-2 py-1 uppercase tracking-wider border-b border-border-subtle/50 mb-0.5">
                  <span>Select Provider & Model</span>
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={async (e) => {
                        e.stopPropagation();
                        try {
                          await fetch('/api/local/open-folder', { method: 'POST' });
                        } catch (err) {
                          console.error('Failed to open models folder', err);
                        }
                      }}
                      className="flex items-center gap-1 text-[9px] hover:text-accent cursor-pointer transition-colors p-0.5 rounded text-text-muted hover:text-text-primary"
                      title="Open project models/ folder in File Explorer to drag & drop GGUF files"
                    >
                      <Folder className="w-2.5 h-2.5 text-accent" />
                      <span>models/</span>
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        fetchModels();
                      }}
                      disabled={isScanningModels}
                      className="flex items-center gap-1 text-[9px] hover:text-accent cursor-pointer transition-colors p-0.5 rounded text-text-muted hover:text-text-primary"
                      title="Rescan models/ folder and HF hub for newly added GGUF models"
                    >
                      <RefreshCw className={`w-2.5 h-2.5 ${isScanningModels ? 'animate-spin' : ''}`} />
                      <span>Rescan</span>
                    </button>
                  </div>
                </div>

                {/* Section: Autonomous Multi-Model Routing */}
                <div className="flex flex-col gap-0.5">
                  <div className="text-[9px] font-mono font-bold uppercase tracking-wider text-accent px-2 py-0.5">
                    🤖 Autonomous Multi-Model Routing
                  </div>
                  {categorizedModelGroups.auto.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      role="option"
                      aria-selected={selectedModel === opt.value}
                      onClick={() => {
                        setSelectedModel(opt.value);
                        setIsModelMenuOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-mono transition-all text-left cursor-pointer btn-press ${
                        selectedModel === opt.value
                          ? 'bg-accent text-accent-contrast font-medium shadow-xs'
                          : 'text-text-primary hover:bg-bg-card-hover'
                      }`}
                    >
                      <span className="truncate">{opt.label}</span>
                      {selectedModel === opt.value && <Check className="w-3.5 h-3.5 shrink-0 ml-1" />}
                    </button>
                  ))}
                </div>

                {/* Section: All-Rounder Models (models/llm/) */}
                {categorizedModelGroups.llm.length > 0 && (
                  <div className="flex flex-col gap-0.5 pt-1 border-t border-border-subtle/30">
                    <div className="text-[9px] font-mono font-bold uppercase tracking-wider text-text-muted px-2 py-0.5 flex items-center justify-between">
                      <span>🧠 All-Rounder Reasoning</span>
                      <span className="text-[8px] font-normal text-text-muted/70">models/llm/</span>
                    </div>
                    {categorizedModelGroups.llm.map((opt) => (
                      <button
                        key={opt.value}
                        type="button"
                        role="option"
                        aria-selected={selectedModel === opt.value}
                        onClick={() => {
                          setSelectedModel(opt.value);
                          setIsModelMenuOpen(false);
                        }}
                        className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-mono transition-all text-left cursor-pointer btn-press ${
                          selectedModel === opt.value
                            ? 'bg-accent text-accent-contrast font-medium shadow-xs'
                            : 'text-text-primary hover:bg-bg-card-hover'
                        }`}
                      >
                        <span className="truncate">{opt.label}</span>
                        {selectedModel === opt.value && <Check className="w-3.5 h-3.5 shrink-0 ml-1" />}
                      </button>
                    ))}
                  </div>
                )}

                {/* Section: Multimodal Vision Models (models/vision/) */}
                {categorizedModelGroups.vision.length > 0 && (
                  <div className="flex flex-col gap-0.5 pt-1 border-t border-border-subtle/30">
                    <div className="text-[9px] font-mono font-bold uppercase tracking-wider text-text-muted px-2 py-0.5 flex items-center justify-between">
                      <span>👁️ Vision & Perception</span>
                      <span className="text-[8px] font-normal text-text-muted/70">models/vision/</span>
                    </div>
                    {categorizedModelGroups.vision.map((opt) => (
                      <button
                        key={opt.value}
                        type="button"
                        role="option"
                        aria-selected={selectedModel === opt.value}
                        onClick={() => {
                          setSelectedModel(opt.value);
                          setIsModelMenuOpen(false);
                        }}
                        className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-mono transition-all text-left cursor-pointer btn-press ${
                          selectedModel === opt.value
                            ? 'bg-accent text-accent-contrast font-medium shadow-xs'
                            : 'text-text-primary hover:bg-bg-card-hover'
                        }`}
                      >
                        <span className="truncate">{opt.label}</span>
                        {selectedModel === opt.value && <Check className="w-3.5 h-3.5 shrink-0 ml-1" />}
                      </button>
                    ))}
                  </div>
                )}

                {/* Section: Connected Cloud Models (Only shown when configured API keys exist) */}
                {categorizedModelGroups.cloud.length > 0 && (
                  <div className="flex flex-col gap-0.5 pt-1 border-t border-border-subtle/30">
                    <div className="text-[9px] font-mono font-bold uppercase tracking-wider text-text-muted px-2 py-0.5">
                      ☁️ Connected Cloud Models
                    </div>
                    {categorizedModelGroups.cloud.map((opt) => (
                      <button
                        key={opt.value}
                        type="button"
                        role="option"
                        aria-selected={selectedModel === opt.value}
                        onClick={() => {
                          setSelectedModel(opt.value);
                          setIsModelMenuOpen(false);
                        }}
                        className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-mono transition-all text-left cursor-pointer btn-press ${
                          selectedModel === opt.value
                            ? 'bg-accent text-accent-contrast font-medium shadow-xs'
                            : 'text-text-primary hover:bg-bg-card-hover'
                        }`}
                      >
                        <span className="truncate">{opt.label}</span>
                        {selectedModel === opt.value && <Check className="w-3.5 h-3.5 shrink-0 ml-1" />}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Synced native select for automated form / test compatibility */}
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="sr-only"
              tabIndex={-1}
              aria-hidden="true"
            >
              <optgroup label="Autonomous Multi-Model Routing">
                {categorizedModelGroups.auto.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </optgroup>
              <optgroup label="All-Rounder Reasoning (models/llm/)">
                {categorizedModelGroups.llm.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </optgroup>
              {categorizedModelGroups.vision.length > 0 && (
                <optgroup label="Vision & Perception (models/vision/)">
                  {categorizedModelGroups.vision.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </optgroup>
              )}
              {categorizedModelGroups.cloud.length > 0 && (
                <optgroup label="Hybrid Cloud Gateways">
                  {categorizedModelGroups.cloud.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </optgroup>
              )}
            </select>
          </div>
        </div>

        {/* Attachment Chips Preview Bar */}
        {attachments.length > 0 && (
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
            {attachments.map((att, i) => (
              <div
                key={i}
                className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-md bg-bg-card-subtle border border-border-subtle text-text-primary"
              >
                <Paperclip className="w-2.5 h-2.5" />
                <span className="truncate max-w-[100px]">{att.name}</span>
                <button
                  onClick={() => removeAttachment(i)}
                  className="hover:text-rose-500 transition-colors ml-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Input Bar */}
        <div className="flex items-center gap-2 bg-bg-card-subtle border border-border-subtle rounded-md px-2.5 py-1.5 focus-within:border-accent focus-within:ring-1 focus-within:ring-accent/30 transition-all">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            multiple
            className="hidden"
          />

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-1.5 rounded-sm text-text-muted hover:text-text-primary hover:bg-bg-card-hover transition-all cursor-pointer shrink-0"
            title="Attach Document or Image"
          >
            <Paperclip className="w-4 h-4" />
          </button>

          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask MaxIM or command computer use..."
            className="flex-1 bg-transparent text-xs text-text-primary placeholder:text-text-muted outline-none font-sans"
          />

          <button
            type="button"
            onClick={handleSend}
            disabled={!inputMessage.trim() && attachments.length === 0}
            className={`p-1.5 rounded-sm transition-all cursor-pointer ${
              inputMessage.trim() || attachments.length > 0
                ? 'bg-accent text-accent-contrast shadow-xs active:scale-95 hover:brightness-110'
                : 'text-text-muted opacity-40 cursor-not-allowed'
            }`}
            title="Send Message"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Image Lightbox Modal */}
      {selectedImage && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-6 animate-in fade-in duration-150">
          <div className="max-w-3xl w-full rounded-2xl border border-border-subtle bg-bg-card p-4 shadow-2xl flex flex-col gap-3">
            <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
              <div className="flex items-center gap-2 text-xs font-semibold text-text-primary">
                <ImageIcon className="w-4 h-4" />
                <span>Generated Image Preview</span>
              </div>
              <button
                onClick={() => setSelectedImage(null)}
                className="p-1 rounded-lg text-text-muted hover:text-text-primary"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="w-full aspect-video rounded-xl overflow-hidden bg-black flex items-center justify-center">
              <img src={selectedImage} alt="Expanded Preview" className="max-h-full object-contain" />
            </div>
          </div>
        </div>
      )}

      {/* Document Reader Modal */}
      {selectedDocument && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-6 animate-in fade-in duration-150">
          <div className="max-w-2xl w-full max-h-[80vh] rounded-2xl border border-border-subtle bg-bg-card p-5 shadow-2xl flex flex-col gap-4">
            <div className="flex items-center justify-between pb-3 border-b border-border-subtle">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-text-primary" />
                <h3 className="text-sm font-semibold text-text-primary">{selectedDocument.title}</h3>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-bg-card-subtle text-text-secondary border border-border-subtle">
                  {selectedDocument.category}
                </span>
              </div>
              <button
                onClick={() => setSelectedDocument(null)}
                className="p-1 rounded-lg text-text-muted hover:text-text-primary"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 rounded-xl bg-bg-card-subtle border border-border-subtle font-mono text-xs text-text-secondary whitespace-pre-wrap leading-relaxed">
              {selectedDocument.fullText}
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
