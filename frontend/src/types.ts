export type TabType = 'home' | 'memory' | 'graph' | 'agents' | 'skills' | 'connections' | 'settings';

export type ThemeMode = 'dark' | 'light';

export type VisualFeedType = 'standby' | 'camera' | 'screen';

export interface HardwareTelemetryData {
  timestamp?: string;
  cpu_percent: number;
  cpu_cores: number;
  ram_total_gb: number;
  ram_used_gb: number;
  ram_free_gb: number;
  ram_percent: number;
  gpu_available?: boolean;
  gpu_name?: string | null;
  vram_total_mb?: number;
  vram_used_mb?: number;
  vram_free_mb?: number;
  vram_percent?: number;
  gpu_temperature_c?: number | null;
  gpu_utilization_percent?: number;
  ollama_online?: boolean;
  ollama_models?: string[];
  latency_ms?: number;
}

export interface ChatAttachment {
  name: string;
  sizeBytes: number;
  type: string;
  dataUrl?: string;
  content?: string;
}

export interface DocumentItem {
  id: string;
  title: string;
  category: string;
  snippet: string;
  fullText: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  timestamp: string;
  thinking?: string;
  attachments?: ChatAttachment[];
  imageUrls?: string[];
  documents?: DocumentItem[];
}

export interface ChatSession {
  id: string;
  title: string;
  updatedAt: string;
  messageCount: number;
}

export interface AgentMember {
  id: string;
  name: string;
  role: string;
  persona: string;
  avatar: string;
  toolsets: string[];
  skills: string[];
  category: string;
  provider: string;
  model: string;
  status: 'idle' | 'active' | 'busy' | 'ready';
  hired_at?: string;
  total_tasks: number;
}

export interface AgentCollaborationGroup {
  id: string;
  name: string;
  description: string;
  member_ids: string[];
  category?: string;
  topic?: string;
  created_at?: string;
}

export interface AgentDispatchLog {
  id: string;
  agentId: string;
  agentName: string;
  task: string;
  status: 'running' | 'completed' | 'failed';
  result: string;
  timestamp: string;
  toolCallsCount?: number;
}

export interface NativeToolItem {
  id: string;
  name: string;
  category: string;
  description: string;
  status: 'active' | 'standby';
  toolset: string;
  parametersCount?: number;
  sampleCall?: string;
}

export interface MCPServerItem {
  id: string;
  name: string;
  description: string;
  registry: 'official' | 'smithery' | 'glama' | 'local';
  transport: 'stdio' | 'sse';
  command?: string;
  args?: string[];
  packageName?: string;
  toolsCount?: number;
  installed: boolean;
  env?: string[];
}

export interface ChannelItem {
  id: string;
  name: string;
  type: 'telegram' | 'discord' | 'slack' | 'webhook' | 'obsidian' | 'agent_reach';
  description: string;
  enabled: boolean;
  status: 'online' | 'configured' | 'standby' | 'disconnected';
  hasToken: boolean;
  hasWebhook: boolean;
  target?: string;
  allowedIdsCount?: number;
  inboundCount: number;
  outboundCount: number;
  lastActive?: string;
  botUsername?: string;
  webhookUrl?: string;
}

export interface InboxLogItem {
  id: number | string;
  channel: string;
  direction: 'inbound' | 'outbound';
  sender_id: string;
  sender_name?: string;
  content: string;
  status: string;
  timestamp: string;
}

export interface ProviderSettingItem {
  id: string;
  name: string;
  category: 'local' | 'cloud' | 'custom';
  defaultModel: string;
  baseUrl?: string;
  apiKey?: string;
  configured: boolean;
  models: string[];
}

export interface VoiceSettingsItem {
  voiceId: string;
  rate: string;
  autoSpeak: boolean;
  sarcasmEnabled: boolean;
  volume: number;
  latencyMode?: 'turbo' | 'studio';
}

export interface PersonalitySettingsItem {
  mode: 'muted' | 'gentle' | 'balanced' | 'proactive';
  cooldownSeconds: number;
  archetype: 'bitterbot' | 'chief_operator' | 'silent_executor';
  sarcasmLevel: number;
}




