import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  User,
  Sparkles,
  Send,
  Compass,
  Eye,
  Moon,
  Volume2,
  VolumeX,
  RefreshCw,
  Cpu,
  Layers,
  ChevronDown,
  ChevronRight,
  Terminal,
  Zap,
  CheckCircle2,
  RotateCcw,
  Target,
  Network,
  Database,
  Search,
  Globe,
  Radio,
  ExternalLink,
  BookOpen,
  GitBranch,
  Star,
  Users,
  Briefcase,
  Plus,
  MessageSquare,
  Play,
  Shield,
  Clock,
  Trash2,
  UserPlus,
  Mic,
  MicOff,
  MessageCircle,
  Sliders,
  X,
  Newspaper,
  Lock,
  Languages,
  Activity,
  Gauge,
  DollarSign,
  HardDrive,
  Check,
  AlertTriangle,
} from 'lucide-react';

interface AgentMember {
  id: string;
  name: string;
  role: string;
  persona: string;
  avatar: string;
  toolsets: string[];
  provider?: string | null;
  model?: string | null;
  status: string;
  hired_at: string;
  total_tasks: number;
}

interface AgentCollaborationGroup {
  id: string;
  name: string;
  description: string;
  member_ids: string[];
  topic?: string | null;
  created_at: string;
}

interface GroupMessage {
  id: number;
  group_id: string;
  sender_id: string;
  sender_name: string;
  role: string;
  content: string;
  timestamp: string;
}

interface ShiftReportItem {
  id: string;
  agent_id: string;
  agent_name: string;
  task: string;
  status: string;
  summary: string;
  timestamp: string;
  evidence_receipts?: any[];
}

interface Receipt {
  tool: string;
  args: Record<string, any>;
  output: string;
}

interface ScoutReportItem {
  id: string;
  created_at: string;
  trigger_type: string;
  topics: string[];
  title: string;
  summary: string;
  briefing_markdown: string;
  audio_brief: string;
  raw_sources?: any[];
  vault_path?: string;
  is_reviewed: boolean;
}

interface InterestTopicItem {
  id: number;
  topic: string;
  category: string;
  weight: number;
  source: string;
  last_seen: string;
}

interface PrivacyStatusData {
  owner_name: string;
  strict_mode: boolean;
  block_all_egress_leaks: boolean;
  redact_file_paths: boolean;
  redact_credentials: boolean;
  redact_pii: boolean;
  total_scans: number;
  total_redactions: number;
  blocked_leak_attempts: number;
  loyalty_status: string;
  egress_guard: string;
}

interface PrivacyAuditLogItem {
  id: number;
  timestamp: string;
  channel: string;
  original_text: string;
  sanitized_text: string;
  blocked: boolean;
  reason: string;
  redactions_count: number;
}

interface LearnedPhraseItem {
  id?: number;
  word_or_phrase: string;
  language: string;
  meaning: string;
  phonetic_script?: string;
  usage_example?: string;
  times_heard: number;
  times_used: number;
  confidence: number;
  source: string;
  learned_at: string;
  last_heard_at: string;
}

interface LanguageStatsData {
  total_vocabulary: number;
  languages: Record<string, number>;
  total_times_heard: number;
  total_times_used: number;
  top_phrases: any[];
  status: string;
}

interface HardwareTelemetryData {
  timestamp: string;
  cpu_percent: number;
  cpu_cores: number;
  ram_total_gb: number;
  ram_used_gb: number;
  ram_free_gb: number;
  ram_percent: number;
  gpu_available: boolean;
  gpu_name?: string | null;
  vram_total_mb: number;
  vram_used_mb: number;
  vram_free_mb: number;
  vram_percent: number;
  gpu_temperature_c?: number | null;
  gpu_utilization_percent: number;
  ollama_online: boolean;
  ollama_models: string[];
}

interface GovernorSettingsData {
  daily_budget_usd: number;
  hard_cap_enabled: boolean;
  auto_downgrade_to_local: boolean;
  prefer_local_first: boolean;
  vram_headroom_threshold_percent: number;
  updated_at: string;
}

interface CostSummaryData {
  date: string;
  total_turns: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  spend_today_usd: number;
  savings_today_usd: number;
  daily_budget_usd: number;
  remaining_budget_usd: number;
  budget_used_percent: number;
  hard_cap_exceeded: boolean;
  auto_downgrade_active: boolean;
  by_provider: Array<{ provider: string; turns: number; tokens: number; cost_usd: number }>;
}

interface CostLedgerItem {
  id?: number;
  timestamp: string;
  date_str: string;
  session_id: string;
  provider: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  estimated_savings_usd: number;
  task_complexity: string;
  routing_decision: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  receipts?: Receipt[];
  statusText?: string;
  timestamp: string;
}

interface TELOSData {
  targets: string[];
  execution: string[];
  lore: string[];
  operations: string[];
  stack: string[];
  raw_content?: string;
}

interface ScreenInfo {
  active_window?: string;
  resolution?: number[];
  image_base64?: string;
  screenshot_available?: boolean;
}

interface ProviderInfo {
  name: string;
  base_url: string;
  model_name: string;
  configured: boolean;
  is_active: boolean;
}

export const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'telos' | 'screen' | 'dream' | 'subagents' | 'memory' | 'reach' | 'operator' | 'scout'>('chat');
  
  // Backend State
  const [backendOnline, setBackendOnline] = useState(false);
  const [sessionId, setSessionId] = useState('default_session');
  const [providers, setProviders] = useState<Record<string, ProviderInfo>>({});
  const [activeProvider, setActiveProvider] = useState('ollama');
  const [connectionRoles, setConnectionRoles] = useState<Record<string, any>>({});
  const [telos, setTelos] = useState<TELOSData | null>(null);
  const [screenInfo, setScreenInfo] = useState<ScreenInfo | null>(null);
  const [morningGreeting, setMorningGreeting] = useState('');
  const [audioPlaying, setAudioPlaying] = useState<string | null>(null);
  const [expandedReceipts, setExpandedReceipts] = useState<Record<string, boolean>>({});

  // Subagent State
  const [subagentTask, setSubagentTask] = useState('');
  const [subagentRole, setSubagentRole] = useState('Vault Archaeologist');
  const [subagentToolset, setSubagentToolset] = useState('vault');
  const [isSubagentRunning, setIsSubagentRunning] = useState(false);
  const [subagentResults, setSubagentResults] = useState<any[]>([]);

  // Zylos 5-Layer Inside-Out Memory & Context Safeguard State
  const [fiveLayers, setFiveLayers] = useState<any | null>(null);
  const [safeguardStatus, setSafeguardStatus] = useState<any | null>(null);
  const [memorySearchQuery, setMemorySearchQuery] = useState('');
  const [memorySearchResults, setMemorySearchResults] = useState<any[]>([]);
  const [isCompacting, setIsCompacting] = useState(false);

  // Agent Reach Native Internet Gateway State
  const [reachDoctor, setReachDoctor] = useState<any | null>(null);
  const [isDoctorRunning, setIsDoctorRunning] = useState(false);
  const [reachSubTab, setReachSubTab] = useState<'fetcher' | 'search' | 'github' | 'community'>('fetcher');
  const [fetchUrl, setFetchUrl] = useState('');
  const [fetchMaxChars, setFetchMaxChars] = useState(10000);
  const [isFetchingUrl, setIsFetchingUrl] = useState(false);
  const [fetchResult, setFetchResult] = useState<any | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchingWeb, setIsSearchingWeb] = useState(false);
  const [webSearchResults, setWebSearchResults] = useState<any | null>(null);
  const [githubRepo, setGithubRepo] = useState('Panniantong/Agent-Reach');
  const [githubAction, setGithubAction] = useState<'info' | 'readme'>('info');
  const [isFetchingGithub, setIsFetchingGithub] = useState(false);
  const [githubResult, setGithubResult] = useState<any | null>(null);
  const [communitySource, setCommunitySource] = useState<'v2ex' | 'hackernews'>('v2ex');
  const [isFetchingCommunity, setIsFetchingCommunity] = useState(false);
  const [communityDiscussions, setCommunityDiscussions] = useState<any[]>([]);

  // Phase 11: LobeHub Chief Agent Operator & Multi-Agent Collaboration Groups State
  const [operatorSubTab, setOperatorSubTab] = useState<'roster' | 'groups' | 'shifts'>('roster');
  const [teamMembers, setTeamMembers] = useState<AgentMember[]>([]);
  const [isLoadingTeam, setIsLoadingTeam] = useState(false);
  const [operatorGroups, setOperatorGroups] = useState<AgentCollaborationGroup[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState<string>('group_core_council');
  const [groupMessages, setGroupMessages] = useState<GroupMessage[]>([]);
  const [isLoadingGroupMessages, setIsLoadingGroupMessages] = useState(false);
  const [groupChatPrompt, setGroupChatPrompt] = useState('');
  const [groupRounds, setGroupRounds] = useState(1);
  const [isGroupChatting, setIsGroupChatting] = useState(false);
  const [shiftReports, setShiftReports] = useState<ShiftReportItem[]>([]);
  const [selectedShiftAgentId, setSelectedShiftAgentId] = useState('agent_chief');
  const [shiftTaskInput, setShiftTaskInput] = useState('Conduct an autonomous system health & architecture check.');
  const [isExecutingShift, setIsExecutingShift] = useState(false);

  // Hire Agent Modal/Form State
  const [showHireModal, setShowHireModal] = useState(false);
  const [hireName, setHireName] = useState('');
  const [hireRole, setHireRole] = useState('');
  const [hirePersona, setHirePersona] = useState('');
  const [hireAvatar, setHireAvatar] = useState('Sparkles');
  const [hireToolsets, setHireToolsets] = useState<string[]>(['vault']);

  // Create Group Modal/Form State
  const [showCreateGroupModal, setShowCreateGroupModal] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupDesc, setNewGroupDesc] = useState('');
  const [newGroupTopic, setNewGroupTopic] = useState('');
  const [newGroupMembers, setNewGroupMembers] = useState<string[]>(['agent_chief']);

  // Phase 12: Proactive Situational Initiative & Real-Time Hands-Free Voice State
  const [isHandsFreeVoiceActive, setIsHandsFreeVoiceActive] = useState(false);
  const isHandsFreeVoiceRef = useRef(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [proactiveThought, setProactiveThought] = useState<any | null>(null);
  const [proactiveSettings, setProactiveSettings] = useState<any>({ mode: 'balanced', auto_speak: true, cooldown_minutes: 8 });
  const [showProactiveSettings, setShowProactiveSettings] = useState(false);
  const [isEvaluatingProactive, setIsEvaluatingProactive] = useState(false);
  const recognitionRef = useRef<any>(null);

  // Autonomous Overnight & Idle Intelligence Scout State
  const [scoutLatestReport, setScoutLatestReport] = useState<ScoutReportItem | null>(null);
  const [scoutReports, setScoutReports] = useState<ScoutReportItem[]>([]);
  const [scoutInterests, setScoutInterests] = useState<InterestTopicItem[]>([]);
  const [scoutStatus, setScoutStatus] = useState<any>({ is_idle: false, is_night: false, minutes_idle: 0 });
  const [isTriggeringScout, setIsTriggeringScout] = useState(false);
  const [newCustomTopic, setNewCustomTopic] = useState('');
  const [newCustomCategory, setNewCustomCategory] = useState('tech');

  // Privacy Guard & Owner Loyalty Protection State
  const [privacyStatus, setPrivacyStatus] = useState<PrivacyStatusData | null>(null);
  const [privacyAuditLogs, setPrivacyAuditLogs] = useState<PrivacyAuditLogItem[]>([]);
  const [isPrivacyModalOpen, setIsPrivacyModalOpen] = useState(false);
  const [isUpdatingPrivacy, setIsUpdatingPrivacy] = useState(false);

  // Adaptive Language Acquisition (Bangla, Chakma, Dialects) State
  const [learnedVocabulary, setLearnedVocabulary] = useState<LearnedPhraseItem[]>([]);
  const [languageStats, setLanguageStats] = useState<LanguageStatsData | null>(null);
  const [isLanguageModalOpen, setIsLanguageModalOpen] = useState(false);
  const [speechRecognitionLang, setSpeechRecognitionLang] = useState<'en-US' | 'bn-BD'>('en-US');
  const [languageFilter, setLanguageFilter] = useState<'all' | 'bangla' | 'chakma'>('all');
  const [newPhraseWord, setNewPhraseWord] = useState('');
  const [newPhraseLang, setNewPhraseLang] = useState('bangla');
  const [newPhraseMeaning, setNewPhraseMeaning] = useState('');
  const [newPhraseExample, setNewPhraseExample] = useState('');
  const [isSubmittingPhrase, setIsSubmittingPhrase] = useState(false);
  const [isSyncingVaultLang, setIsSyncingVaultLang] = useState(false);
  const [langVaultSyncedMessage, setLangVaultSyncedMessage] = useState<string | null>(null);

  // OpenJarvis Hardware & Cost Governor State
  const [hardwareTelemetry, setHardwareTelemetry] = useState<HardwareTelemetryData | null>(null);
  const [governorSettings, setGovernorSettings] = useState<GovernorSettingsData | null>(null);
  const [governorSummary, setGovernorSummary] = useState<CostSummaryData | null>(null);
  const [costLedger, setCostLedger] = useState<CostLedgerItem[]>([]);
  const [isGovernorModalOpen, setIsGovernorModalOpen] = useState(false);
  const [isUpdatingGovernor, setIsUpdatingGovernor] = useState(false);
  const [editBudgetUsd, setEditBudgetUsd] = useState<number>(1.0);
  const [editHardCap, setEditHardCap] = useState<boolean>(true);
  const [editPreferLocal, setEditPreferLocal] = useState<boolean>(true);
  const [editAutoDowngrade, setEditAutoDowngrade] = useState<boolean>(true);

  useEffect(() => {
    isHandsFreeVoiceRef.current = isHandsFreeVoiceActive;
  }, [isHandsFreeVoiceActive]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  // Initial Data Fetch
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('/api/health');
        if (res.ok) {
          const data = await res.json();
          setBackendOnline(true);
          setActiveProvider(data.active_provider);
        } else {
          setBackendOnline(false);
        }
      } catch {
        setBackendOnline(false);
      }
    };

    const fetchProviders = async () => {
      try {
        const res = await fetch('/api/providers');
        if (res.ok) {
          const data = await res.json();
          setProviders(data.providers);
          setActiveProvider(data.active_provider);
        }
      } catch (err) {
        console.error('Failed to fetch providers', err);
      }
    };

    const fetchTelos = async () => {
      try {
        const res = await fetch('/api/telos');
        if (res.ok) {
          const data = await res.json();
          setTelos(data.profile);
        }
      } catch (err) {
        console.error('Failed to fetch TELOS', err);
      }
    };

    const fetchMorning = async () => {
      try {
        const res = await fetch('/api/morning-greeting');
        if (res.ok) {
          const data = await res.json();
          setMorningGreeting(data.greeting);
        }
      } catch (err) {
        console.error('Failed to fetch morning greeting', err);
      }
    };

    const fetchScreen = async () => {
      try {
        const res = await fetch('/api/screen');
        if (res.ok) {
          const data = await res.json();
          setScreenInfo(data);
        }
      } catch (err) {
        console.error('Failed to fetch screen info', err);
      }
    };

    const fetchConnections = async () => {
      try {
        const res = await fetch('/api/connections');
        if (res.ok) {
          const data = await res.json();
          setConnectionRoles(data.roles || {});
        }
      } catch (err) {
        console.error('Failed to fetch connections', err);
      }
    };

    checkHealth();
    fetchProviders();
    fetchTelos();
    fetchMorning();
    fetchScreen();
    fetchConnections();
    fetchFiveLayers();
    fetchScoutLatest();
    fetchScoutStatus();
    fetchPrivacyStatus();
    fetchLanguageVocabulary();
    fetchHardwareTelemetry();
    fetchGovernorData();

    const telemetryInterval = setInterval(() => {
      fetchHardwareTelemetry();
      fetchGovernorData();
    }, 15000);

    return () => clearInterval(telemetryInterval);
  }, [sessionId]);

  const fetchFiveLayers = async () => {
    try {
      const res = await fetch(`/api/memory/five-layers?session_id=${sessionId}`);
      if (res.ok) {
        const data = await res.json();
        setFiveLayers(data);
        if (data.safeguard_status) {
          setSafeguardStatus(data.safeguard_status);
        }
      }
    } catch (err) {
      console.error('Failed to fetch 5 layers', err);
    }
  };

  const handleSearchMemory = async () => {
    if (!memorySearchQuery.trim()) return;
    try {
      const res = await fetch('/api/memory/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: memorySearchQuery, limit: 8 }),
      });
      if (res.ok) {
        const data = await res.json();
        setMemorySearchResults(data.results || []);
      }
    } catch (err) {
      console.error('Failed to search memory', err);
    }
  };

  const handleTriggerCompaction = async () => {
    setIsCompacting(true);
    try {
      const res = await fetch('/api/memory/compact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, reason: 'Manual 75% safeguard trigger from UI' }),
      });
      if (res.ok) {
        await fetchFiveLayers();
      }
    } catch (err) {
      console.error('Failed to trigger safeguard compaction', err);
    } finally {
      setIsCompacting(false);
    }
  };

  // Agent Reach Native Internet Gateway Handlers
  const runReachDoctor = async () => {
    setIsDoctorRunning(true);
    try {
      const res = await fetch('/api/reach/doctor');
      if (res.ok) {
        const data = await res.json();
        setReachDoctor(data);
      }
    } catch (e) {
      console.error('Reach doctor failed:', e);
    } finally {
      setIsDoctorRunning(false);
    }
  };

  const handleFetchUrl = async () => {
    if (!fetchUrl.trim()) return;
    setIsFetchingUrl(true);
    try {
      const res = await fetch('/api/reach/read', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: fetchUrl.trim(), max_chars: fetchMaxChars }),
      });
      if (res.ok) {
        const data = await res.json();
        setFetchResult(data);
      }
    } catch (e) {
      console.error('Fetch URL failed:', e);
    } finally {
      setIsFetchingUrl(false);
    }
  };

  const handleWebSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearchingWeb(true);
    try {
      const res = await fetch('/api/reach/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery.trim(), max_results: 6 }),
      });
      if (res.ok) {
        const data = await res.json();
        setWebSearchResults(data);
      }
    } catch (e) {
      console.error('Web search failed:', e);
    } finally {
      setIsSearchingWeb(false);
    }
  };

  const handleGithubReach = async () => {
    if (!githubRepo.trim()) return;
    setIsFetchingGithub(true);
    try {
      const res = await fetch('/api/reach/github', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo: githubRepo.trim(), action: githubAction }),
      });
      if (res.ok) {
        const data = await res.json();
        setGithubResult(data);
      }
    } catch (e) {
      console.error('GitHub reach failed:', e);
    } finally {
      setIsFetchingGithub(false);
    }
  };

  const handleCommunityReach = async (source?: 'v2ex' | 'hackernews') => {
    const src = source || communitySource;
    setIsFetchingCommunity(true);
    try {
      const res = await fetch(`/api/reach/community?source=${src}&limit=8`);
      if (res.ok) {
        const data = await res.json();
        setCommunityDiscussions(data.items || data.discussions || []);
      }
    } catch (e) {
      console.error('Community reach failed:', e);
    } finally {
      setIsFetchingCommunity(false);
    }
  };

  // Switch Provider
  const handleSelectProvider = async (pName: string) => {
    try {
      const res = await fetch('/api/providers/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: pName }),
      });
      if (res.ok) {
        const data = await res.json();
        setActiveProvider(data.active_provider);
        // Refresh provider list
        const pRes = await fetch('/api/providers');
        if (pRes.ok) {
          const pData = await pRes.json();
          setProviders(pData.providers);
        }
      }
    } catch (err) {
      console.error('Error selecting provider', err);
    }
  };

  // Trigger Dream
  const handleTriggerDream = async () => {
    try {
      const res = await fetch('/api/dream/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      });
      if (res.ok) {
        // Refresh morning greeting and telos
        const mRes = await fetch('/api/morning-greeting');
        if (mRes.ok) {
          const mData = await mRes.json();
          setMorningGreeting(mData.greeting);
        }
      }
    } catch (err) {
      console.error('Failed to trigger dream cycle', err);
    }
  };

  // Refresh Screen Capture
  const handleRefreshScreen = async () => {
    try {
      const res = await fetch('/api/screen');
      if (res.ok) {
        const data = await res.json();
        setScreenInfo(data);
      }
    } catch (err) {
      console.error('Failed to refresh screen', err);
    }
  };

  const handleSpawnSubagent = async () => {
    if (!subagentTask.trim() || isSubagentRunning) return;
    setIsSubagentRunning(true);
    try {
      const res = await fetch('/api/subagent/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: subagentTask,
          role: subagentRole,
          toolset: subagentToolset,
          max_iterations: 4,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setSubagentResults((prev) => [data, ...prev]);
        setSubagentTask('');
      }
    } catch (err) {
      console.error('Failed to spawn subagent', err);
    } finally {
      setIsSubagentRunning(false);
    }
  };

  // =========================================================================
  // Phase 11: LobeHub Chief Agent Operator & Multi-Agent Collaboration Handlers
  // =========================================================================

  const fetchTeamMembers = async () => {
    setIsLoadingTeam(true);
    try {
      const res = await fetch('/api/operator/team');
      if (res.ok) {
        const data = await res.json();
        setTeamMembers(data.team || []);
      }
    } catch (err) {
      console.error('Failed to fetch operator team', err);
    } finally {
      setIsLoadingTeam(false);
    }
  };

  const handleHireAgent = async () => {
    if (!hireName.trim() || !hireRole.trim() || !hirePersona.trim()) return;
    try {
      const res = await fetch('/api/operator/hire', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: hireName.trim(),
          role: hireRole.trim(),
          persona: hirePersona.trim(),
          avatar: hireAvatar,
          toolsets: hireToolsets,
        }),
      });
      if (res.ok) {
        await fetchTeamMembers();
        setShowHireModal(false);
        setHireName('');
        setHireRole('');
        setHirePersona('');
      }
    } catch (err) {
      console.error('Failed to hire agent', err);
    }
  };

  const handleFireAgent = async (agentId: string) => {
    try {
      const res = await fetch(`/api/operator/team/${agentId}`, { method: 'DELETE' });
      if (res.ok) {
        await fetchTeamMembers();
      }
    } catch (err) {
      console.error('Failed to fire agent', err);
    }
  };

  const fetchOperatorGroups = async () => {
    try {
      const res = await fetch('/api/operator/groups');
      if (res.ok) {
        const data = await res.json();
        const groups = data.groups || [];
        setOperatorGroups(groups);
        if (groups.length > 0) {
          const currentId = groups.some((g: any) => g.id === selectedGroupId)
            ? selectedGroupId
            : groups[0].id;
          setSelectedGroupId(currentId);
          fetchGroupMessages(currentId);
        }
      }
    } catch (err) {
      console.error('Failed to fetch operator groups', err);
    }
  };

  const fetchGroupMessages = async (groupId: string) => {
    setIsLoadingGroupMessages(true);
    try {
      const res = await fetch(`/api/operator/groups/${groupId}/messages?limit=50`);
      if (res.ok) {
        const data = await res.json();
        setGroupMessages(data.messages || []);
      }
    } catch (err) {
      console.error('Failed to fetch group messages', err);
    } finally {
      setIsLoadingGroupMessages(false);
    }
  };

  const handleCreateGroup = async () => {
    if (!newGroupName.trim() || !newGroupDesc.trim() || newGroupMembers.length === 0) return;
    try {
      const res = await fetch('/api/operator/groups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newGroupName.trim(),
          description: newGroupDesc.trim(),
          member_ids: newGroupMembers,
          topic: newGroupTopic.trim() || undefined,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setShowCreateGroupModal(false);
        setNewGroupName('');
        setNewGroupDesc('');
        setNewGroupTopic('');
        await fetchOperatorGroups();
        setSelectedGroupId(data.id);
        fetchGroupMessages(data.id);
      }
    } catch (err) {
      console.error('Failed to create group', err);
    }
  };

  const handleRunGroupChat = async () => {
    if (!groupChatPrompt.trim() || !selectedGroupId || isGroupChatting) return;
    const promptToSend = groupChatPrompt.trim();
    setGroupChatPrompt('');
    setIsGroupChatting(true);

    try {
      const res = await fetch(`/api/operator/groups/${selectedGroupId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: promptToSend,
          rounds: groupRounds,
        }),
      });
      if (res.ok) {
        await fetchGroupMessages(selectedGroupId);
      }
    } catch (err) {
      console.error('Failed to run group chat', err);
    } finally {
      setIsGroupChatting(false);
    }
  };

  const fetchShiftReports = async () => {
    try {
      const res = await fetch('/api/operator/reports?limit=20');
      if (res.ok) {
        const data = await res.json();
        setShiftReports(data.reports || []);
      }
    } catch (err) {
      console.error('Failed to fetch shift reports', err);
    }
  };

  const handleExecuteShift = async () => {
    if (!shiftTaskInput.trim() || isExecutingShift) return;
    setIsExecutingShift(true);
    try {
      const res = await fetch('/api/operator/shifts/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: selectedShiftAgentId,
          task: shiftTaskInput.trim(),
          save_to_vault: true,
        }),
      });
      if (res.ok) {
        await fetchShiftReports();
        await fetchTeamMembers();
      }
    } catch (err) {
      console.error('Failed to execute shift', err);
    } finally {
      setIsExecutingShift(false);
    }
  };

  // =========================================================================
  // Phase 12: Proactive Situational Initiative & Real-Time Hands-Free Voice Handlers
  // =========================================================================

  const fetchProactiveSettings = async () => {
    try {
      const res = await fetch('/api/proactive/settings');
      if (res.ok) {
        const data = await res.json();
        setProactiveSettings(data);
      }
    } catch (e) {
      console.error('Failed to fetch proactive settings', e);
    }
  };

  const handleUpdateProactiveMode = async (mode: string) => {
    try {
      const res = await fetch('/api/proactive/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode }),
      });
      if (res.ok) {
        const data = await res.json();
        setProactiveSettings(data);
      }
    } catch (e) {
      console.error('Failed to update proactive mode', e);
    }
  };

  const handleToggleAutoSpeak = async () => {
    const nextVal = !proactiveSettings.auto_speak;
    try {
      const res = await fetch('/api/proactive/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ auto_speak: nextVal }),
      });
      if (res.ok) {
        const data = await res.json();
        setProactiveSettings(data);
      }
    } catch (e) {
      console.error('Failed to toggle auto-speak', e);
    }
  };

  const evaluateProactiveInitiative = async (force: boolean = false) => {
    if (isEvaluatingProactive) return;
    setIsEvaluatingProactive(true);
    try {
      const res = await fetch('/api/proactive/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, force }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.should_intervene && data.intervention) {
          setProactiveThought(data.intervention);
          if (data.auto_speak && data.intervention.message) {
            handlePlayVoice(`proactive_${data.intervention.id}`, data.intervention.message);
          }
        }
      }
    } catch (e) {
      console.error('Proactive evaluation error', e);
    } finally {
      setIsEvaluatingProactive(false);
    }
  };

  useEffect(() => {
    fetchProactiveSettings();

    const interval = setInterval(() => {
      if (proactiveSettings.mode !== 'muted') {
        evaluateProactiveInitiative(false);
      }
    }, 60000);

    const onFocus = () => {
      if (proactiveSettings.mode !== 'muted') {
        evaluateProactiveInitiative(false);
      }
    };
    window.addEventListener('focus', onFocus);

    return () => {
      clearInterval(interval);
      window.removeEventListener('focus', onFocus);
    };
  }, [sessionId, proactiveSettings.mode]);

  // =========================================================================
  // Autonomous Overnight & Idle Intelligence Scout Handlers
  // =========================================================================

  const fetchScoutStatus = async () => {
    try {
      const res = await fetch('/api/scout/status');
      if (res.ok) {
        const data = await res.json();
        setScoutStatus(data);
      }
    } catch (e) {
      console.error('Failed to fetch scout status', e);
    }
  };

  const fetchScoutLatest = async () => {
    try {
      const res = await fetch('/api/scout/latest');
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'found' && data.report) {
          setScoutLatestReport(data.report);
        }
      }
    } catch (e) {
      console.error('Failed to fetch latest scout report', e);
    }
  };

  const fetchScoutReports = async () => {
    try {
      const res = await fetch('/api/scout/reports?limit=20');
      if (res.ok) {
        const data = await res.json();
        setScoutReports(data.reports || []);
      }
    } catch (e) {
      console.error('Failed to fetch scout reports', e);
    }
  };

  const fetchScoutInterests = async () => {
    try {
      const res = await fetch('/api/scout/interests');
      if (res.ok) {
        const data = await res.json();
        setScoutInterests(data.topics || []);
      }
    } catch (e) {
      console.error('Failed to fetch scout interests', e);
    }
  };

  const handleTriggerScoutCycle = async (triggerType: string = 'manual') => {
    if (isTriggeringScout) return;
    setIsTriggeringScout(true);
    try {
      const res = await fetch('/api/scout/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trigger_type: triggerType, force: true }),
      });
      if (res.ok) {
        const report = await res.json();
        setScoutLatestReport(report);
        await fetchScoutReports();
        await fetchScoutStatus();
      }
    } catch (e) {
      console.error('Failed to trigger scout cycle', e);
    } finally {
      setIsTriggeringScout(false);
    }
  };

  const handleAddCustomInterest = async () => {
    if (!newCustomTopic.trim()) return;
    try {
      const res = await fetch('/api/scout/interests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: newCustomTopic.trim(), category: newCustomCategory }),
      });
      if (res.ok) {
        setNewCustomTopic('');
        await fetchScoutInterests();
      }
    } catch (e) {
      console.error('Failed to add custom interest', e);
    }
  };

  const handleDeleteInterestTopic = async (topicId: number) => {
    try {
      const res = await fetch(`/api/scout/interests/${topicId}`, { method: 'DELETE' });
      if (res.ok) {
        await fetchScoutInterests();
      }
    } catch (e) {
      console.error('Failed to delete interest topic', e);
    }
  };

  const handleReviewScoutReport = async (reportId: string) => {
    try {
      const res = await fetch(`/api/scout/reports/${reportId}/review`, { method: 'POST' });
      if (res.ok) {
        setScoutLatestReport((prev) => (prev ? { ...prev, is_reviewed: true } : null));
        fetchScoutReports();
      }
    } catch (e) {
      console.error('Failed to review scout report', e);
    }
  };

  // =========================================================================
  // Privacy Guard & Owner Loyalty Protection Handlers
  // =========================================================================

  const fetchPrivacyStatus = async () => {
    try {
      const res = await fetch('/api/privacy/status');
      if (res.ok) {
        const data = await res.json();
        setPrivacyStatus(data);
      }
    } catch (e) {
      console.error('Failed to fetch privacy status', e);
    }
  };

  const fetchPrivacyAuditLogs = async () => {
    try {
      const res = await fetch('/api/privacy/audit?limit=25');
      if (res.ok) {
        const data = await res.json();
        setPrivacyAuditLogs(data.audit_logs || []);
      }
    } catch (e) {
      console.error('Failed to fetch privacy audit logs', e);
    }
  };

  const handleTogglePrivacyStrict = async () => {
    if (!privacyStatus) return;
    setIsUpdatingPrivacy(true);
    try {
      const res = await fetch('/api/privacy/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strict_mode: !privacyStatus.strict_mode }),
      });
      if (res.ok) {
        await fetchPrivacyStatus();
      }
    } catch (e) {
      console.error('Failed to toggle privacy strict mode', e);
    } finally {
      setIsUpdatingPrivacy(false);
    }
  };

  // =========================================================================
  // Adaptive Language Acquisition (Bangla, Chakma, Dialects) Handlers
  // =========================================================================

  const fetchLanguageVocabulary = async (lang?: string) => {
    try {
      const url = lang && lang !== 'all' ? `/api/languages/vocabulary?language=${lang}` : '/api/languages/vocabulary';
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setLearnedVocabulary(data.vocabulary || []);
        setLanguageStats(data.stats || null);
      }
    } catch (e) {
      console.error('Failed to fetch language vocabulary', e);
    }
  };

  const handleTeachPhrase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPhraseWord.trim() || !newPhraseMeaning.trim()) return;
    setIsSubmittingPhrase(true);
    try {
      const res = await fetch('/api/languages/learn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          word_or_phrase: newPhraseWord.trim(),
          language: newPhraseLang,
          meaning: newPhraseMeaning.trim(),
          usage_example: newPhraseExample.trim() || undefined,
        }),
      });
      if (res.ok) {
        setNewPhraseWord('');
        setNewPhraseMeaning('');
        setNewPhraseExample('');
        await fetchLanguageVocabulary(languageFilter);
      }
    } catch (e) {
      console.error('Failed to teach phrase', e);
    } finally {
      setIsSubmittingPhrase(false);
    }
  };

  const handleSyncLanguagesToVault = async () => {
    setIsSyncingVaultLang(true);
    try {
      const res = await fetch('/api/languages/sync-vault', { method: 'POST' });
      if (res.ok) {
        setLangVaultSyncedMessage('Exported to vault/02 - Knowledge/Learned Languages & Dialects.md');
        setTimeout(() => setLangVaultSyncedMessage(null), 4000);
      }
    } catch (e) {
      console.error('Failed to sync languages to vault', e);
    } finally {
      setIsSyncingVaultLang(false);
    }
  };

  // =========================================================================
  // OpenJarvis Hardware Telemetry & Cost Governor Handlers
  // =========================================================================

  const fetchHardwareTelemetry = async () => {
    try {
      const res = await fetch('/api/hardware/telemetry');
      if (res.ok) {
        const data = await res.json();
        setHardwareTelemetry(data);
      }
    } catch (e) {
      console.error('Failed to fetch hardware telemetry', e);
    }
  };

  const fetchGovernorData = async () => {
    try {
      const res = await fetch('/api/hardware/governor');
      if (res.ok) {
        const data = await res.json();
        setGovernorSummary(data.summary);
        setGovernorSettings(data.settings);
        if (data.settings) {
          setEditBudgetUsd(data.settings.daily_budget_usd);
          setEditHardCap(data.settings.hard_cap_enabled);
          setEditPreferLocal(data.settings.prefer_local_first);
          setEditAutoDowngrade(data.settings.auto_downgrade_to_local);
        }
      }
    } catch (e) {
      console.error('Failed to fetch governor data', e);
    }
  };

  const fetchCostLedger = async () => {
    try {
      const res = await fetch('/api/hardware/cost-ledger?limit=30');
      if (res.ok) {
        const data = await res.json();
        setCostLedger(data.ledger || []);
      }
    } catch (e) {
      console.error('Failed to fetch cost ledger', e);
    }
  };

  const handleUpdateGovernorSettings = async () => {
    setIsUpdatingGovernor(true);
    try {
      const res = await fetch('/api/hardware/governor/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          daily_budget_usd: editBudgetUsd,
          hard_cap_enabled: editHardCap,
          prefer_local_first: editPreferLocal,
          auto_downgrade_to_local: editAutoDowngrade,
        }),
      });
      if (res.ok) {
        await fetchGovernorData();
      }
    } catch (e) {
      console.error('Failed to update governor settings', e);
    } finally {
      setIsUpdatingGovernor(false);
    }
  };

  const startSpeechRecognition = () => {
    const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRec) return;

    try {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
        recognitionRef.current = null;
      }

      const recognition = new SpeechRec();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = speechRecognitionLang;

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        let currentTranscript = '';
        let isFinal = false;

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const chunk = event.results[i][0].transcript;
          currentTranscript += chunk;
          if (event.results[i].isFinal) {
            isFinal = true;
          }
        }

        setVoiceTranscript(currentTranscript);

        if (isFinal && currentTranscript.trim().length > 1) {
          const finalQuery = currentTranscript.trim();
          setVoiceTranscript('');
          try {
            recognition.stop();
          } catch {}
          setIsListening(false);
          handleSendMessage(finalQuery);
        }
      };

      recognition.onerror = (event: any) => {
        console.warn('Speech recognition error:', event.error);
        if (event.error === 'no-speech' || event.error === 'network') {
          // Normal background silence or brief network dip
        } else {
          setIsListening(false);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
        // Only restart if hands-free is active AND no assistant audio is currently playing
        if (isHandsFreeVoiceRef.current && !audioRef.current) {
          setTimeout(() => {
            if (isHandsFreeVoiceRef.current && !audioRef.current) {
              startSpeechRecognition();
            }
          }, 300);
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
      setIsListening(true);
    } catch (err) {
      console.error('Failed to start speech recognition', err);
      setIsListening(false);
    }
  };

  const toggleHandsFreeVoice = () => {
    const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRec) {
      alert('Your browser does not support Web Speech Recognition. Please use Chrome, Edge, or Brave for hands-free voice.');
      return;
    }

    if (isHandsFreeVoiceActive) {
      isHandsFreeVoiceRef.current = false;
      setIsHandsFreeVoiceActive(false);
      setIsListening(false);
      setVoiceTranscript('');
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
        recognitionRef.current = null;
      }
    } else {
      isHandsFreeVoiceRef.current = true;
      setIsHandsFreeVoiceActive(true);
      startSpeechRecognition();
    }
  };

  const handleNewSession = async () => {
    try {
      const res = await fetch('/api/session/new', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setSessionId(data.session_id);
        setMessages([]);
      }
    } catch (err) {
      console.error('Failed to create new session', err);
    }
  };

  // Play Neural Voice with hands-free turn-taking management
  const handlePlayVoice = async (msgId: string, text: string) => {
    if (audioPlaying === msgId) {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      setAudioPlaying(null);
      if (isHandsFreeVoiceRef.current) {
        startSpeechRecognition();
      }
      return;
    }

    // Stop microphone while assistant speaks to prevent acoustic echo
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {}
      setIsListening(false);
    }

    try {
      setAudioPlaying(msgId);
      const res = await fetch('/api/voice/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });

      if (!res.ok) throw new Error('Audio synthesis failed');
      const blob = await res.blob();
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onended = () => {
        setAudioPlaying(null);
        audioRef.current = null;
        // Resume continuous listening automatically for the next user utterance
        if (isHandsFreeVoiceRef.current) {
          setTimeout(() => {
            if (isHandsFreeVoiceRef.current && !audioRef.current) {
              startSpeechRecognition();
            }
          }, 300);
        }
      };

      audio.onerror = () => {
        setAudioPlaying(null);
        audioRef.current = null;
        if (isHandsFreeVoiceRef.current) {
          startSpeechRecognition();
        }
      };

      audio.play();
    } catch (err) {
      console.error('Audio playback error', err);
      setAudioPlaying(null);
      audioRef.current = null;
      if (isHandsFreeVoiceRef.current) {
        startSpeechRecognition();
      }
    }
  };

  // Send Chat Message with SSE Streaming
  const handleSendMessage = async (textToSend?: string) => {
    const userPrompt = (textToSend || input).trim();
    if (!userPrompt || isStreaming) return;

    setInput('');
    const userMsgId = `user_${Date.now()}`;
    const assistantMsgId = `asst_${Date.now()}`;

    const newMessages: Message[] = [
      ...messages,
      {
        id: userMsgId,
        role: 'user',
        content: userPrompt,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
      {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        statusText: 'Analyzing intent against TELOS...',
        receipts: [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ];

    setMessages(newMessages);
    setIsStreaming(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userPrompt,
          session_id: sessionId,
          stream: true,
        }),
      });

      if (!res.ok || !res.body) {
        throw new Error(`Server returned ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let accumulatedContent = '';
      let collectedReceipts: Receipt[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data:')) {
            const rawJson = trimmed.slice(5).trim();
            if (!rawJson) continue;

            try {
              const event = JSON.parse(rawJson);
              if (event.type === 'status') {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId ? { ...m, statusText: event.message } : m
                  )
                );
              } else if (event.type === 'tool_call') {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? { ...m, statusText: `Executing: ${event.tool}...` }
                      : m
                  )
                );
              } else if (event.type === 'tool_result') {
                collectedReceipts.push({
                  tool: event.tool,
                  args: {},
                  output: typeof event.output === 'string' ? event.output : JSON.stringify(event.output),
                });
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? { ...m, receipts: [...collectedReceipts], statusText: `Executed ${event.tool}` }
                      : m
                  )
                );
              } else if (event.type === 'content') {
                accumulatedContent += event.content;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? { ...m, content: accumulatedContent, statusText: undefined }
                      : m
                  )
                );
              } else if (event.type === 'done') {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? { ...m, statusText: undefined }
                      : m
                  )
                );
                if (isHandsFreeVoiceRef.current && accumulatedContent.trim()) {
                  handlePlayVoice(assistantMsgId, accumulatedContent.trim());
                }
              }
            } catch (parseErr) {
              console.warn('Could not parse SSE event chunk:', rawJson, parseErr);
            }
          }
        }
      }
    } catch (err: any) {
      console.error('Chat stream error:', err);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId
            ? { ...m, content: `Error communicating with MaxIM: ${err.message}`, statusText: undefined }
            : m
        )
      );
    } finally {
      setIsStreaming(false);
    }
  };

  const toggleReceiptExpand = (receiptKey: string) => {
    setExpandedReceipts((prev) => ({ ...prev, [receiptKey]: !prev[receiptKey] }));
  };

  return (
    <div className="flex h-screen w-screen bg-[#07090e] text-slate-100 font-sans overflow-hidden select-none">
      {/* LEFT NAVIGATION BAR */}
      <aside className="w-16 border-r border-white/5 bg-[#0a0d14]/80 flex flex-col items-center py-5 justify-between z-20">
        <div className="flex flex-col items-center gap-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-sky-400 p-[1px] shadow-lg shadow-cyan-500/20">
            <div className="w-full h-full bg-[#07090e] rounded-[11px] flex items-center justify-center text-cyan-400">
              <Sparkles className="w-5 h-5 animate-pulse" />
            </div>
          </div>

          <nav className="flex flex-col gap-3">
            <button
              onClick={() => setActiveTab('chat')}
              className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                activeTab === 'chat'
                  ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 shadow-md shadow-cyan-500/10'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
              title="Chat Feed"
            >
              <Bot className="w-5 h-5" />
            </button>

            <button
              onClick={() => setActiveTab('telos')}
              className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                activeTab === 'telos'
                  ? 'bg-purple-500/15 text-purple-400 border border-purple-500/30 shadow-md shadow-purple-500/10'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
              title="LifeOS TELOS Intent"
            >
              <Target className="w-5 h-5" />
            </button>

            <button
              onClick={() => setActiveTab('screen')}
              className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                activeTab === 'screen'
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-md shadow-emerald-500/10'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
              title="Screen Perception"
            >
              <Eye className="w-5 h-5" />
            </button>

            <button
              onClick={() => setActiveTab('dream')}
              className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                activeTab === 'dream'
                  ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30 shadow-md shadow-amber-500/10'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
              title="Bitterbot Dream Engine"
            >
              <Moon className="w-5 h-5" />
            </button>

            <button
              onClick={() => setActiveTab('subagents')}
              className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                activeTab === 'subagents'
                  ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-md shadow-sky-500/10'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
              title="Sub-Agent Delegation & Multi-Connection"
            >
              <Network className="w-5 h-5" />
            </button>

            <button
              onClick={() => {
                setActiveTab('memory');
                fetchFiveLayers();
              }}
              className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                activeTab === 'memory'
                  ? 'bg-purple-500/15 text-purple-400 border border-purple-500/30 shadow-md shadow-purple-500/10'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
              title="Zylos 5-Layer Inside-Out Memory & Context Safeguard"
            >
              <Database className="w-5 h-5" />
            </button>

            <button
              onClick={() => {
                setActiveTab('reach');
                if (!reachDoctor) {
                  runReachDoctor();
                }
                if (communityDiscussions.length === 0) {
                  handleCommunityReach('v2ex');
                }
              }}
              className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                activeTab === 'reach'
                  ? 'bg-blue-500/15 text-blue-400 border border-blue-500/30 shadow-md shadow-blue-500/10'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
              title="Agent Reach Native Internet Gateway"
            >
              <Globe className="w-5 h-5" />
            </button>

            <button
              onClick={() => {
                setActiveTab('operator');
                fetchTeamMembers();
                fetchOperatorGroups();
                fetchShiftReports();
              }}
              className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                activeTab === 'operator'
                  ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 shadow-md shadow-indigo-500/10'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
              title="LobeHub Chief Agent Operator & Multi-Agent Collaboration Groups"
            >
              <Users className="w-5 h-5" />
            </button>

            <button
              onClick={() => {
                setActiveTab('scout');
                fetchScoutStatus();
                fetchScoutLatest();
                fetchScoutReports();
                fetchScoutInterests();
              }}
              className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                activeTab === 'scout'
                  ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30 shadow-md shadow-amber-500/10'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
              title="Autonomous Overnight & Idle Intelligence Scout"
            >
              <Newspaper className="w-5 h-5" />
            </button>
          </nav>
        </div>

        <div className="flex flex-col items-center gap-3">
          <div
            className={`w-2.5 h-2.5 rounded-full ${
              backendOnline ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-rose-500 animate-ping'
            }`}
            title={backendOnline ? 'Backend Online (Port 8000)' : 'Backend Disconnected'}
          />
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col h-full bg-[#07090e] overflow-hidden">
        {/* TOP STATUS HEADER */}
        <header className="h-14 border-b border-white/5 bg-[#0a0d14]/50 backdrop-blur-md px-6 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <span className="font-semibold text-sm tracking-wide text-white">MaxIM</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-950/60 border border-cyan-800/40 text-cyan-300 font-mono">
              v2.0 Native
            </span>
            <span className="text-xs text-slate-500">|</span>
            <span className="text-xs text-slate-400 font-mono">
              {telos?.targets?.[0] ? `Active: ${telos.targets[0]}` : 'Intent: LifeOS TELOS'}
            </span>
          </div>

          <div className="flex items-center gap-4">
            {/* ZYLOS CONTEXT SAFEGUARD PILL */}
            {safeguardStatus && (
              <div
                onClick={() => {
                  setActiveTab('memory');
                  fetchFiveLayers();
                }}
                className={`cursor-pointer flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[11px] font-mono transition-all ${
                  safeguardStatus.triggered
                    ? 'bg-rose-500/10 border-rose-500/30 text-rose-400 animate-pulse'
                    : safeguardStatus.capacity_percent > 50
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                    : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                }`}
                title={`Context Usage: ${safeguardStatus.estimated_tokens} / ${safeguardStatus.max_tokens} tokens (${safeguardStatus.capacity_percent}%). Click to inspect.`}
              >
                <Layers className="w-3 h-3" />
                <span>{safeguardStatus.capacity_percent}% Ctx</span>
              </div>
            )}

            {/* PROVIDER SELECTOR */}
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-slate-400" />
              <select
                value={activeProvider}
                onChange={(e) => handleSelectProvider(e.target.value)}
                className="bg-[#10141f] border border-white/10 text-xs rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none focus:border-cyan-500 transition-colors font-mono cursor-pointer"
              >
                {Object.keys(providers).map((pKey) => (
                  <option key={pKey} value={pKey}>
                    {pKey.toUpperCase()} ({providers[pKey].model_name})
                  </option>
                ))}
              </select>
            </div>

            {/* PRIVACY GUARD & OWNER LOYALTY SHIELD */}
            <button
              onClick={() => {
                fetchPrivacyStatus();
                fetchPrivacyAuditLogs();
                setIsPrivacyModalOpen(true);
              }}
              className="px-2.5 py-1.5 rounded-lg border text-xs font-mono flex items-center gap-1.5 transition-all cursor-pointer bg-emerald-500/10 border-emerald-500/25 text-emerald-300 hover:bg-emerald-500/20 shadow-sm shadow-emerald-500/10"
              title="Privacy Guard Active: Owner Protected (Sam) | Zero-Egress Sandbox"
            >
              <Shield className="w-3.5 h-3.5 text-emerald-400" />
              <span className="hidden sm:inline">Protected: {privacyStatus?.owner_name || 'Sam'}</span>
              {privacyStatus && privacyStatus.blocked_leak_attempts > 0 && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full bg-rose-500/20 text-rose-400 text-[10px]">
                  {privacyStatus.blocked_leak_attempts}
                </span>
              )}
            </button>

            {/* ADAPTIVE LOCAL LANGUAGES & DIALECTS (BANGLA, CHAKMA) */}
            <button
              onClick={() => {
                fetchLanguageVocabulary();
                setIsLanguageModalOpen(true);
              }}
              className="px-2.5 py-1.5 rounded-lg border text-xs font-mono flex items-center gap-1.5 transition-all cursor-pointer bg-indigo-500/10 border-indigo-500/25 text-indigo-300 hover:bg-indigo-500/20 shadow-sm shadow-indigo-500/10"
              title="Adaptive Linguistic Ear: Learned Bangla, Chakma & Regional Dialects"
            >
              <Languages className="w-3.5 h-3.5 text-indigo-400" />
              <span className="hidden md:inline">Dialects: {languageStats?.total_vocabulary || learnedVocabulary.length || 15}</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-indigo-500/20 text-indigo-300 font-mono">
                BN/CK
              </span>
            </button>

            {/* SPEECH RECOGNITION LANGUAGE TOGGLE */}
            <div className="hidden lg:flex items-center rounded-lg border border-white/10 bg-black/40 p-0.5 text-[10px] font-mono">
              <button
                onClick={() => setSpeechRecognitionLang('en-US')}
                className={`px-2 py-0.5 rounded transition-colors cursor-pointer ${
                  speechRecognitionLang === 'en-US'
                    ? 'bg-cyan-500/20 text-cyan-300 font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
                title="Voice Input: English (en-US)"
              >
                EN
              </button>
              <button
                onClick={() => setSpeechRecognitionLang('bn-BD')}
                className={`px-2 py-0.5 rounded transition-colors cursor-pointer ${
                  speechRecognitionLang === 'bn-BD'
                    ? 'bg-amber-500/20 text-amber-300 font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
                title="Voice Input: Bangla (bn-BD)"
              >
                বাংলা
              </button>
            </div>

            {/* OPENJARVIS HARDWARE & COST GOVERNOR PILL */}
            <button
              onClick={() => {
                fetchHardwareTelemetry();
                fetchGovernorData();
                fetchCostLedger();
                setIsGovernorModalOpen(true);
              }}
              className={`px-2.5 py-1.5 rounded-lg border text-xs font-mono flex items-center gap-1.5 transition-all cursor-pointer ${
                governorSummary?.hard_cap_exceeded
                  ? 'bg-rose-500/15 border-rose-500/40 text-rose-300 animate-pulse'
                  : 'bg-cyan-500/10 border-cyan-500/25 text-cyan-300 hover:bg-cyan-500/20 shadow-sm shadow-cyan-500/10'
              }`}
              title="OpenJarvis Hardware & Cost Governor: CPU/RAM/VRAM & Real-Time LLM Budget"
            >
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
              <span className="hidden xl:inline">
                {hardwareTelemetry?.gpu_available ? `GPU ${hardwareTelemetry.vram_percent}%` : `CPU ${hardwareTelemetry?.cpu_percent || 0}%`}
              </span>
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-cyan-500/20 text-cyan-200 font-mono">
                ${governorSummary?.spend_today_usd?.toFixed(2) || '0.00'} / ${governorSettings?.daily_budget_usd?.toFixed(2) || '1.00'}
              </span>
            </button>

            {/* REAL-TIME HANDS-FREE VOICE TOGGLE */}
            <button
              onClick={toggleHandsFreeVoice}
              className={`px-2.5 py-1.5 rounded-lg border text-xs font-mono flex items-center gap-1.5 transition-all cursor-pointer ${
                isHandsFreeVoiceActive
                  ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300 shadow-md shadow-emerald-500/20 animate-pulse'
                  : 'bg-white/5 border-white/10 text-slate-400 hover:text-slate-200'
              }`}
              title={
                isHandsFreeVoiceActive
                  ? 'Hands-Free Voice is Active (Auto-Listens & Speaks)'
                  : 'Enable Continuous Hands-Free Voice'
              }
            >
              {isHandsFreeVoiceActive ? (
                <Mic className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <MicOff className="w-3.5 h-3.5 text-slate-400" />
              )}
              <span className="hidden sm:inline">
                {isHandsFreeVoiceActive ? 'Voice Hands-Free' : 'Voice Off'}
              </span>
            </button>

            {/* PROACTIVE INITIATIVE SENSITIVITY SELECTOR */}
            <div className="relative">
              <button
                onClick={() => setShowProactiveSettings(!showProactiveSettings)}
                className="px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-mono text-cyan-300 flex items-center gap-1.5 transition-colors cursor-pointer"
                title="Proactive Initiative & Situation Evaluation Settings"
              >
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                <span className="capitalize hidden md:inline">
                  {proactiveSettings.mode || 'balanced'}
                </span>
                <Sliders className="w-3 h-3 text-slate-400" />
              </button>

              {showProactiveSettings && (
                <div className="absolute right-0 mt-2 w-72 p-3.5 bg-[#10141f] border border-white/15 rounded-2xl shadow-2xl z-50 space-y-3 font-sans backdrop-blur-xl">
                  <div className="flex items-center justify-between pb-2 border-b border-white/5">
                    <span className="text-xs font-semibold text-white flex items-center gap-1.5 font-mono">
                      <Sparkles className="w-3.5 h-3.5 text-cyan-400" /> Proactive Initiative
                    </span>
                    <button
                      onClick={() => setShowProactiveSettings(false)}
                      className="text-slate-400 hover:text-white p-1 rounded-md"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[11px] text-slate-400 block font-mono">
                      Sensitivity Mode
                    </label>
                    <div className="grid grid-cols-2 gap-1.5">
                      {(['gentle', 'balanced', 'proactive', 'muted'] as const).map((m) => (
                        <button
                          key={m}
                          onClick={() => handleUpdateProactiveMode(m)}
                          className={`px-2 py-1.5 rounded-lg text-xs capitalize font-mono border transition-all ${
                            proactiveSettings.mode === m
                              ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-200 shadow-sm'
                              : 'bg-white/5 border-white/5 text-slate-400 hover:text-slate-200'
                          }`}
                        >
                          {m}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-1 border-t border-white/5 text-xs text-slate-300">
                    <div>
                      <div className="font-mono text-[11px] text-slate-200">Auto-Speak Voice</div>
                      <div className="text-[10px] text-slate-400">Speak out proactive ideas</div>
                    </div>
                    <input
                      type="checkbox"
                      checked={!!proactiveSettings.auto_speak}
                      onChange={handleToggleAutoSpeak}
                      className="w-4 h-4 rounded accent-cyan-500 cursor-pointer"
                    />
                  </div>

                  <div className="pt-2 border-t border-white/5">
                    <button
                      onClick={() => {
                        evaluateProactiveInitiative(true);
                        setShowProactiveSettings(false);
                      }}
                      disabled={isEvaluatingProactive}
                      className="w-full py-2 px-3 bg-gradient-to-r from-cyan-600 to-sky-600 hover:from-cyan-500 hover:to-sky-500 disabled:opacity-50 text-white rounded-xl text-xs font-mono flex items-center justify-center gap-1.5 transition-all shadow-md shadow-cyan-900/30"
                    >
                      {isEvaluatingProactive ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Sparkles className="w-3.5 h-3.5" />
                      )}
                      <span>
                        {isEvaluatingProactive ? 'Evaluating Situation...' : 'Check Situation Now'}
                      </span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* QUICK ACTIONS */}
            <button
              onClick={handleNewSession}
              className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 text-slate-300 transition-all text-xs flex items-center gap-1.5"
              title="Start New Session"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleRefreshScreen}
              className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 text-slate-300 transition-all text-xs flex items-center gap-1.5"
              title="Refresh Screen Capture"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </header>

        {/* DYNAMIC VIEW ROUTER */}
        {activeTab === 'chat' && (
          <div className="flex-1 flex flex-col h-[calc(100vh-3.5rem)]">
            {/* MORNING GREETING BANNER */}
            {morningGreeting && (
              <div className="mx-6 mt-4 p-3.5 rounded-xl bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/20 flex items-start gap-3">
                <Moon className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
                <div className="flex-1 text-xs text-amber-200/90 leading-relaxed font-sans">
                  <span className="font-semibold text-amber-400 font-mono mr-1.5">BITTERBOT BRIEF:</span>
                  {morningGreeting}
                </div>
              </div>
            )}

            {/* OVERNIGHT INTELLIGENCE SCOUT BANNER */}
            {scoutLatestReport && !scoutLatestReport.is_reviewed && (
              <div className="mx-6 mt-3 p-4 rounded-2xl bg-gradient-to-r from-amber-950/70 via-orange-950/50 to-[#10141f] border border-amber-500/30 backdrop-blur-md flex items-start justify-between gap-4 shadow-xl shadow-amber-950/20 animate-in fade-in slide-in-from-top-2 duration-300">
                <div className="flex items-start gap-3.5">
                  <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-300 shrink-0 mt-0.5 shadow-md shadow-amber-500/10">
                    <Moon className="w-5 h-5 text-amber-400" />
                  </div>
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-mono uppercase tracking-wider text-amber-400 font-semibold">
                        Overnight Intelligence Briefing Ready
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/25">
                        {scoutLatestReport.topics?.length || 0} Topics Scouted
                      </span>
                    </div>
                    <div className="text-xs font-semibold text-white">
                      {scoutLatestReport.title}
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed font-sans line-clamp-2">
                      {scoutLatestReport.summary}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => handlePlayVoice(`scout_${scoutLatestReport.id}`, scoutLatestReport.audio_brief)}
                    className="p-2 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 transition-all flex items-center gap-1.5 text-xs font-mono cursor-pointer"
                    title="Listen to Morning Audio Brief"
                  >
                    <Volume2 className="w-4 h-4" />
                    <span className="hidden sm:inline">Listen</span>
                  </button>
                  <button
                    onClick={() => {
                      setActiveTab('scout');
                      fetchScoutStatus();
                      fetchScoutLatest();
                    }}
                    className="px-3 py-2 rounded-xl bg-white/10 hover:bg-white/15 border border-white/15 text-xs font-mono text-white transition-all flex items-center gap-1.5 cursor-pointer"
                  >
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>View Intel</span>
                  </button>
                  <button
                    onClick={() => handleReviewScoutReport(scoutLatestReport.id)}
                    className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors cursor-pointer"
                    title="Dismiss"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* MESSAGE STREAM */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-5">
              {messages.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 max-w-lg mx-auto">
                  <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-4">
                    <Sparkles className="w-6 h-6" />
                  </div>
                  <h2 className="text-base font-semibold text-white mb-2">MaxIM ReAct Engine Online</h2>
                  <p className="text-xs text-slate-400 leading-relaxed mb-6">
                    Direct access to Obsidian vault, computer use actions, and multi-model routing.
                    Type a query or trigger one of the intent actions below.
                  </p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    <button
                      onClick={() => handleSendMessage("What are my active targets in TELOS?")}
                      className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 text-xs text-slate-300 transition-all font-mono"
                    >
                      🎯 Check TELOS Targets
                    </button>
                    <button
                      onClick={() => handleSendMessage("What is currently on my screen?")}
                      className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 text-xs text-slate-300 transition-all font-mono"
                    >
                      🖥️ Inspect Active Screen
                    </button>
                    <button
                      onClick={() => handleSendMessage("Search the Obsidian vault for recent notes")}
                      className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 text-xs text-slate-300 transition-all font-mono"
                    >
                      📖 Search Vault Notes
                    </button>
                  </div>
                </div>
              )}

              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3.5 max-w-3xl ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}
                >
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                      msg.role === 'user'
                        ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30'
                        : 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/25'
                    }`}
                  >
                    {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>

                  <div className="flex-1 space-y-2">
                    <div
                      className={`p-4 rounded-2xl text-xs leading-relaxed ${
                        msg.role === 'user'
                          ? 'bg-sky-600/15 border border-sky-500/30 text-sky-100 rounded-tr-none'
                          : 'bg-[#10141f] border border-white/10 text-slate-200 rounded-tl-none shadow-xl'
                      }`}
                    >
                      {/* STATUS OR THINKING TEXT */}
                      {msg.statusText && (
                        <div className="flex items-center gap-2 mb-2 text-cyan-400 font-mono text-[11px] animate-pulse">
                          <Terminal className="w-3.5 h-3.5" />
                          <span>{msg.statusText}</span>
                        </div>
                      )}

                      {/* MAIN CONTENT */}
                      <div className="whitespace-pre-wrap font-sans">{msg.content}</div>

                      {/* EXECUTION RECEIPTS (Meta Muse Pattern) */}
                      {msg.receipts && msg.receipts.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-white/5 space-y-2">
                          <div className="text-[10px] font-mono text-slate-400 flex items-center gap-1.5 uppercase tracking-wider">
                            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                            <span>Execution Receipts ({msg.receipts.length})</span>
                          </div>
                          {msg.receipts.map((r, idx) => {
                            const key = `${msg.id}_rec_${idx}`;
                            const isExp = expandedReceipts[key];
                            return (
                              <div
                                key={key}
                                className="rounded-lg bg-black/40 border border-white/5 overflow-hidden text-[11px] font-mono"
                              >
                                <button
                                  onClick={() => toggleReceiptExpand(key)}
                                  className="w-full px-2.5 py-1.5 flex items-center justify-between text-slate-400 hover:text-slate-200 transition-colors"
                                >
                                  <span className="text-cyan-400">tool: {r.tool}</span>
                                  {isExp ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                                </button>
                                {isExp && (
                                  <div className="p-2.5 bg-black/60 border-t border-white/5 text-slate-300 max-h-36 overflow-y-auto whitespace-pre-wrap">
                                    {r.output}
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    {/* ASSISTANT AUDIO CONTROLS & TIMESTAMP */}
                    {msg.role === 'assistant' && msg.content && (
                      <div className="flex items-center gap-3 px-1">
                        <button
                          onClick={() => handlePlayVoice(msg.id, msg.content)}
                          className="flex items-center gap-1 text-[11px] font-mono text-slate-400 hover:text-cyan-400 transition-colors"
                        >
                          {audioPlaying === msg.id ? (
                            <>
                              <VolumeX className="w-3 h-3 text-cyan-400 animate-pulse" />
                              <span className="text-cyan-400">Stop Voice</span>
                            </>
                          ) : (
                            <>
                              <Volume2 className="w-3 h-3" />
                              <span>Speak Voice</span>
                            </>
                          )}
                        </button>
                        <span className="text-[10px] text-slate-600 font-mono">{msg.timestamp}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* PROACTIVE INITIATIVE SITUATIONAL INTERVENTION BANNER */}
            {proactiveThought && (
              <div className="mx-6 mb-3 p-3.5 rounded-xl bg-gradient-to-r from-cyan-950/80 via-[#0d1527]/90 to-purple-950/80 border border-cyan-500/30 backdrop-blur-md shadow-xl flex items-start justify-between gap-3 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-300 shrink-0 mt-0.5 shadow-sm">
                    <Sparkles className="w-4 h-4 animate-pulse text-cyan-400" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-mono uppercase tracking-wider text-cyan-400 font-semibold">
                        MaxIM Proactive Thought
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                        {proactiveThought.trigger_reason || 'Situational Alignment'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-100 font-sans leading-relaxed">
                      {proactiveThought.message}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  <button
                    onClick={() => handlePlayVoice(`proactive_${proactiveThought.id}`, proactiveThought.message)}
                    className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-cyan-300 transition-colors"
                    title="Speak thought aloud"
                  >
                    <Volume2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => {
                      setInput(`Regarding "${proactiveThought.message}": `);
                    }}
                    className="px-2.5 py-1 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-[11px] font-medium text-cyan-200 transition-colors flex items-center gap-1 font-mono"
                  >
                    <MessageCircle className="w-3 h-3" />
                    <span>Reply</span>
                  </button>
                  <button
                    onClick={() => setProactiveThought(null)}
                    className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-slate-200 transition-colors"
                    title="Dismiss"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}

            {/* LIVE HANDS-FREE TRANSCRIPT BANNER */}
            {isListening && (
              <div className="mx-6 mb-2 px-3.5 py-2 rounded-xl bg-emerald-950/40 border border-emerald-500/30 backdrop-blur-md flex items-center justify-between gap-3 text-xs font-mono animate-pulse shadow-lg shadow-emerald-950/20">
                <div className="flex items-center gap-2.5 text-emerald-400">
                  <Mic className="w-4 h-4 animate-bounce text-emerald-300" />
                  <span>
                    {voiceTranscript ? (
                      <span>Heard: <span className="text-white font-sans italic font-normal">"{voiceTranscript}"</span></span>
                    ) : (
                      'Listening in real time... Speak naturally.'
                    )}
                  </span>
                </div>
                <button
                  onClick={toggleHandsFreeVoice}
                  className="text-[10px] text-emerald-400/80 hover:text-emerald-200 underline cursor-pointer"
                >
                  Turn Off
                </button>
              </div>
            )}

            {/* INPUT BAR */}
            <div className="p-4 border-t border-white/5 bg-[#0a0d14]/70 backdrop-blur-md">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="flex items-center gap-2 max-w-4xl mx-auto"
              >
                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={
                      isStreaming
                        ? 'MaxIM is executing...'
                        : isHandsFreeVoiceActive
                        ? 'Hands-free voice active. Speak aloud or type...'
                        : 'Ask MaxIM or command computer use...'
                    }
                    disabled={isStreaming}
                    className="w-full bg-[#10141f] border border-white/10 rounded-xl px-4 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/30 transition-all font-sans"
                  />
                </div>
                <button
                  type="button"
                  onClick={toggleHandsFreeVoice}
                  className={`p-3 rounded-xl border text-xs transition-all flex items-center justify-center cursor-pointer ${
                    isHandsFreeVoiceActive
                      ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300 shadow-md shadow-emerald-500/20 animate-pulse'
                      : 'bg-white/5 border-white/10 text-slate-400 hover:text-slate-200 hover:bg-white/10'
                  }`}
                  title={
                    isHandsFreeVoiceActive
                      ? 'Hands-Free Voice Active (Click to disable)'
                      : 'Enable Hands-Free Continuous Voice'
                  }
                >
                  {isHandsFreeVoiceActive ? (
                    <Mic className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <MicOff className="w-4 h-4" />
                  )}
                </button>
                <button
                  type="submit"
                  disabled={isStreaming || !input.trim()}
                  className="px-4 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-sky-500 text-white text-xs font-medium hover:from-cyan-400 hover:to-sky-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-cyan-500/20 flex items-center gap-1.5"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </div>
          </div>
        )}

        {/* TELOS LIFEOS TAB */}
        {activeTab === 'telos' && (
          <div className="flex-1 overflow-y-auto p-8 max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
              <div>
                <h1 className="text-lg font-semibold text-white">LifeOS TELOS Intent</h1>
                <p className="text-xs text-slate-400">
                  Daniel Miessler's framework loaded from <span className="text-cyan-400 font-mono">vault/00 - LifeOS/TELOS.md</span>
                </p>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 font-mono">
                Grounding Active
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-5 rounded-2xl bg-[#10141f] border border-white/5 space-y-3">
                <div className="text-xs font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  <span>Targets (Milestones)</span>
                </div>
                <ul className="space-y-2 text-xs text-slate-300">
                  {telos?.targets?.map((t, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-purple-400 mt-0.5">•</span>
                      <span>{t}</span>
                    </li>
                  )) || <li className="text-slate-500 italic">No targets defined</li>}
                </ul>
              </div>

              <div className="p-5 rounded-2xl bg-[#10141f] border border-white/5 space-y-3">
                <div className="text-xs font-semibold text-sky-400 uppercase tracking-wider flex items-center gap-2">
                  <Zap className="w-4 h-4" />
                  <span>Execution (Projects)</span>
                </div>
                <ul className="space-y-2 text-xs text-slate-300">
                  {telos?.execution?.map((e, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-sky-400 mt-0.5">•</span>
                      <span>{e}</span>
                    </li>
                  )) || <li className="text-slate-500 italic">No execution projects</li>}
                </ul>
              </div>

              <div className="p-5 rounded-2xl bg-[#10141f] border border-white/5 space-y-3">
                <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-2">
                  <Compass className="w-4 h-4" />
                  <span>Lore (Core Truths)</span>
                </div>
                <ul className="space-y-2 text-xs text-slate-300">
                  {telos?.lore?.map((l, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-amber-400 mt-0.5">•</span>
                      <span>{l}</span>
                    </li>
                  )) || <li className="text-slate-500 italic">No core lore defined</li>}
                </ul>
              </div>

              <div className="p-5 rounded-2xl bg-[#10141f] border border-white/5 space-y-3">
                <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                  <Layers className="w-4 h-4" />
                  <span>Operations & Stack</span>
                </div>
                <ul className="space-y-2 text-xs text-slate-300">
                  {telos?.operations?.map((o, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-emerald-400 mt-0.5">•</span>
                      <span>{o}</span>
                    </li>
                  )) || <li className="text-slate-500 italic">No operational rules</li>}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* SCREEN PERCEPTION TAB */}
        {activeTab === 'screen' && (
          <div className="flex-1 overflow-y-auto p-8 max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
              <div>
                <h1 className="text-lg font-semibold text-white">Screen & Window Perception</h1>
                <p className="text-xs text-slate-400">
                  Real-time active window tracking and token-budgeted screen capture
                </p>
              </div>
              <button
                onClick={handleRefreshScreen}
                className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20 transition-all text-xs font-mono flex items-center gap-2"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Capture Now</span>
              </button>
            </div>

            <div className="p-5 rounded-2xl bg-[#10141f] border border-white/5 space-y-4">
              <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                <div>
                  <span className="text-slate-500">Active Window:</span>
                  <div className="text-slate-200 font-semibold mt-1">
                    {screenInfo?.active_window || 'Unknown'}
                  </div>
                </div>
                <div>
                  <span className="text-slate-500">Scaled Resolution:</span>
                  <div className="text-slate-200 mt-1">
                    {screenInfo?.resolution ? `${screenInfo.resolution[0]} × ${screenInfo.resolution[1]}` : 'N/A'}
                  </div>
                </div>
              </div>

              {screenInfo?.image_base64 ? (
                <div className="rounded-xl overflow-hidden border border-white/10 bg-black">
                  <img
                    src={`data:image/jpeg;base64,${screenInfo.image_base64}`}
                    alt="Active Screen Snapshot"
                    className="w-full h-auto object-contain max-h-[500px]"
                  />
                </div>
              ) : (
                <div className="h-64 rounded-xl border border-dashed border-white/10 flex items-center justify-center text-slate-500 text-xs font-mono">
                  No screenshot captured yet.
                </div>
              )}
            </div>
          </div>
        )}

        {/* BITTERBOT DREAM ENGINE TAB */}
        {activeTab === 'dream' && (
          <div className="flex-1 overflow-y-auto p-8 max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
              <div>
                <h1 className="text-lg font-semibold text-white">Bitterbot Dream Engine</h1>
                <p className="text-xs text-slate-400">
                  Offline reflection synthesizing conversation thoughts into Obsidian notes
                </p>
              </div>
              <button
                onClick={handleTriggerDream}
                className="px-3.5 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 hover:bg-amber-500/20 transition-all text-xs font-mono flex items-center gap-2"
              >
                <Moon className="w-3.5 h-3.5" />
                <span>Run Dream Cycle</span>
              </button>
            </div>

            <div className="p-6 rounded-2xl bg-[#10141f] border border-white/5 space-y-4">
              <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-2">
                <Moon className="w-4 h-4" />
                <span>Morning Wake-Up Greeting</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-sans bg-black/40 p-4 rounded-xl border border-white/5">
                {morningGreeting || 'No morning greeting generated yet. Trigger a dream cycle above.'}
              </p>
            </div>
          </div>
        )}

        {/* SUBAGENTS & MULTI-CONNECTION TAB */}
        {activeTab === 'subagents' && (
          <div className="flex-1 overflow-y-auto p-8 max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
              <div>
                <h1 className="text-lg font-semibold text-white">Hermes Sub-Agent Delegation & Connections</h1>
                <p className="text-xs text-slate-400">
                  Spawn isolated child agents with dedicated toolsets and multi-provider model routing
                </p>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 font-mono">
                Hermes Multi-Gateway Active
              </span>
            </div>

            {/* MULTI-CONNECTION ROLES CARD */}
            <div className="p-5 rounded-2xl bg-[#10141f] border border-white/5 space-y-3">
              <div className="text-xs font-semibold text-sky-400 uppercase tracking-wider flex items-center gap-2">
                <Cpu className="w-4 h-4" />
                <span>Configured Connection Roles</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
                {Object.keys(connectionRoles).map((roleKey) => (
                  <div key={roleKey} className="p-3 rounded-xl bg-black/40 border border-white/5">
                    <span className="text-slate-500 uppercase text-[10px]">{roleKey}:</span>
                    <div className="text-white font-semibold mt-0.5">
                      {connectionRoles[roleKey]?.provider || 'default'}
                    </div>
                    <div className="text-[10px] text-cyan-400 truncate">
                      {connectionRoles[roleKey]?.model || 'default'}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* SPAWN SUBAGENT FORM */}
            <div className="p-5 rounded-2xl bg-[#10141f] border border-white/5 space-y-4">
              <div className="text-xs font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
                <Network className="w-4 h-4" />
                <span>Dispatch Specialist Sub-Agent</span>
              </div>
              <div className="space-y-3">
                <textarea
                  value={subagentTask}
                  onChange={(e) => setSubagentTask(e.target.value)}
                  placeholder="Describe the dedicated objective for the sub-agent (e.g., 'Inspect Obsidian vault for notes on DeepSeek and summarize key takeaways')..."
                  className="w-full bg-black/40 border border-white/10 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-sans h-24"
                />
                <div className="flex flex-wrap gap-3 items-center justify-between">
                  <div className="flex items-center gap-3">
                    <select
                      value={subagentRole}
                      onChange={(e) => setSubagentRole(e.target.value)}
                      className="bg-black/60 border border-white/10 text-xs rounded-lg px-3 py-1.5 text-slate-200 font-mono"
                    >
                      <option value="Vault Archaeologist">Role: Vault Archaeologist</option>
                      <option value="Screen Analyst">Role: Screen Analyst</option>
                      <option value="Code Auditor">Role: Code Auditor</option>
                      <option value="General Researcher">Role: General Researcher</option>
                    </select>

                    <select
                      value={subagentToolset}
                      onChange={(e) => setSubagentToolset(e.target.value)}
                      className="bg-black/60 border border-white/10 text-xs rounded-lg px-3 py-1.5 text-slate-200 font-mono"
                    >
                      <option value="vault">Toolset: Vault Only</option>
                      <option value="perception">Toolset: Perception Only</option>
                      <option value="cua">Toolset: CUA Automation</option>
                      <option value="all">Toolset: Full System Tools</option>
                    </select>
                  </div>

                  <button
                    onClick={handleSpawnSubagent}
                    disabled={isSubagentRunning || !subagentTask.trim()}
                    className="px-4 py-2 rounded-xl bg-gradient-to-r from-sky-500 to-cyan-500 text-white text-xs font-medium hover:from-sky-400 hover:to-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-sky-500/20 flex items-center gap-2"
                  >
                    <Network className="w-3.5 h-3.5" />
                    <span>{isSubagentRunning ? 'Executing Sub-Agent...' : 'Spawn & Execute Sub-Agent'}</span>
                  </button>
                </div>
              </div>
            </div>

            {/* SUBAGENT EXECUTION FEED */}
            {subagentResults.length > 0 && (
              <div className="space-y-4">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Completed Sub-Agent Missions ({subagentResults.length})
                </div>
                {subagentResults.map((sub, i) => (
                  <div key={i} className="p-5 rounded-2xl bg-[#10141f] border border-white/5 space-y-3">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <div className="flex items-center gap-2">
                        <span className="text-cyan-400 font-semibold">{sub.role}</span>
                        <span className="text-slate-500 text-[10px]">({sub.subagent_id})</span>
                      </div>
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px]">
                        {sub.status} ({sub.iterations || 1} steps)
                      </span>
                    </div>
                    <div className="text-xs text-slate-400 font-sans italic border-l-2 border-white/10 pl-3">
                      "{sub.task}"
                    </div>
                    <div className="text-xs text-slate-200 leading-relaxed font-sans bg-black/40 p-4 rounded-xl border border-white/5 whitespace-pre-wrap">
                      {sub.result}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ZYLOS FIVE-LAYER MEMORY & CONTEXT SAFEGUARD TAB */}
        {activeTab === 'memory' && (
          <div className="flex-1 overflow-y-auto p-8 max-w-5xl mx-auto space-y-6">
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
              <div>
                <h1 className="text-lg font-semibold text-white">Zylos Inside-Out Memory Architecture</h1>
                <p className="text-xs text-slate-400">
                  Five-layer contextual grounding with SQLite FTS5 BM25 search and 75% safeguard compaction
                </p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={fetchFiveLayers}
                  className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 text-slate-300 transition-all text-xs flex items-center gap-1.5"
                  title="Refresh Memory Snapshot"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Refresh</span>
                </button>
                <button
                  onClick={handleTriggerCompaction}
                  disabled={isCompacting}
                  className="px-3.5 py-1.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 hover:bg-purple-500/20 disabled:opacity-40 transition-all text-xs font-mono flex items-center gap-2"
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span>{isCompacting ? 'Compacting...' : 'Trigger 75% Safeguard'}</span>
                </button>
              </div>
            </div>

            {/* CONTEXT SAFEGUARD GAUGE CARD */}
            {safeguardStatus && (
              <div className="p-5 rounded-2xl bg-[#10141f] border border-white/5 space-y-3">
                <div className="flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400 uppercase text-[10px] tracking-wider">Context Window Capacity</span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] border ${
                      safeguardStatus.triggered
                        ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                        : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                    }`}>
                      {safeguardStatus.status}
                    </span>
                  </div>
                  <span className="text-slate-300">
                    {safeguardStatus.estimated_tokens} / {safeguardStatus.max_tokens} tokens ({safeguardStatus.capacity_percent}%)
                  </span>
                </div>
                <div className="w-full h-3 rounded-full bg-black/60 border border-white/5 overflow-hidden relative">
                  <div
                    className={`h-full transition-all duration-500 ${
                      safeguardStatus.triggered
                        ? 'bg-gradient-to-r from-amber-500 to-rose-500'
                        : safeguardStatus.capacity_percent > 50
                        ? 'bg-gradient-to-r from-cyan-500 to-amber-500'
                        : 'bg-gradient-to-r from-sky-500 to-emerald-400'
                    }`}
                    style={{ width: `${Math.min(100, safeguardStatus.capacity_percent)}%` }}
                  />
                  {/* 75% Marker Line */}
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-rose-500 shadow-[0_0_4px_#f43f5e]"
                    style={{ left: '75%' }}
                    title="75% Safeguard Threshold"
                  />
                </div>
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
                  <span>0 Tokens</span>
                  <span className="text-rose-400 font-semibold">▲ 75% Compaction Safeguard Threshold</span>
                  <span>{safeguardStatus.max_tokens} Tokens</span>
                </div>
              </div>
            )}

            {/* BM25 FULL-TEXT SEARCH */}
            <div className="p-5 rounded-2xl bg-[#10141f] border border-white/5 space-y-3">
              <div className="text-xs font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-2">
                <Search className="w-4 h-4" />
                <span>SQLite FTS5 BM25 Instant Search</span>
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={memorySearchQuery}
                  onChange={(e) => setMemorySearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearchMemory()}
                  placeholder="Search across all memory facts, turns, and Obsidian vault notes..."
                  className="flex-1 bg-black/40 border border-white/10 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 font-sans"
                />
                <button
                  onClick={handleSearchMemory}
                  className="px-4 py-2 rounded-xl bg-purple-600/30 border border-purple-500/30 text-purple-300 text-xs font-medium hover:bg-purple-600/40 transition-all flex items-center gap-1.5"
                >
                  <Search className="w-3.5 h-3.5" />
                  <span>Search</span>
                </button>
              </div>

              {memorySearchResults.length > 0 && (
                <div className="space-y-2 mt-3 pt-3 border-t border-white/5">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider font-mono">
                    Search Matches ({memorySearchResults.length})
                  </span>
                  {memorySearchResults.map((m, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-black/40 border border-white/5 text-xs space-y-1">
                      <div className="flex items-center justify-between text-[11px] font-mono">
                        <span className="text-purple-300 font-semibold">{m.title}</span>
                        <span className="px-2 py-0.5 rounded bg-white/5 text-slate-400 text-[10px]">
                          Layer {m.layer}: {m.source}
                        </span>
                      </div>
                      <div className="text-slate-400 text-[11px] line-clamp-2 font-sans">
                        {m.content}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* THE FIVE LAYERS CARDS GRID */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* LAYER 1 */}
              <div className="p-5 rounded-2xl bg-[#10141f] border border-white/5 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
                    <Target className="w-4 h-4" />
                    <span>Layer 1: Identity & Persona</span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 font-mono">
                    Permanent Anchor
                  </span>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                    <div className="text-[10px] text-slate-500 font-mono">SOUL.MD CONTRACT:</div>
                    <div className="text-slate-200 mt-1">
                      {fiveLayers?.layer_1_identity?.soul_contract_loaded ? 'Active (Bitterbot Personality)' : 'Default'}
                      <span className="text-slate-500 ml-2 font-mono">({fiveLayers?.layer_1_identity?.soul_length || 0} chars)</span>
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                    <div className="text-[10px] text-slate-500 font-mono">LIFEOS TELOS TARGETS:</div>
                    <div className="text-slate-200 mt-1 line-clamp-2">
                      {fiveLayers?.layer_1_identity?.telos_targets?.[0] || 'No primary target configured'}
                    </div>
                  </div>
                </div>
              </div>

              {/* LAYER 2 */}
              <div className="p-5 rounded-2xl bg-[#10141f] border border-white/5 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                    <Eye className="w-4 h-4" />
                    <span>Layer 2: State & Perception</span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono">
                    Real-Time Context
                  </span>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                    <div className="text-[10px] text-slate-500 font-mono">ACTIVE FOCUSED WINDOW:</div>
                    <div className="text-slate-200 mt-1 font-mono truncate">
                      {fiveLayers?.layer_2_state?.active_window || 'Desktop / No Window'}
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                    <div className="text-[10px] text-slate-500 font-mono">DISPLAY RESOLUTION:</div>
                    <div className="text-slate-200 mt-1 font-mono">
                      {fiveLayers?.layer_2_state?.resolution?.join(' x ') || '1280 x 720'}
                    </div>
                  </div>
                </div>
              </div>

              {/* LAYER 3 */}
              <div className="p-5 rounded-2xl bg-[#10141f] border border-white/5 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold text-sky-400 uppercase tracking-wider flex items-center gap-2">
                    <Layers className="w-4 h-4" />
                    <span>Layer 3: References & Obsidian Graph</span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 font-mono">
                    {fiveLayers?.layer_3_references?.vault_note_count || 0} Vault Notes
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-black/40 border border-white/5 text-xs space-y-1.5 max-h-36 overflow-y-auto">
                  {fiveLayers?.layer_3_references?.references?.map((r: any, i: number) => (
                    <div key={i} className="flex items-center justify-between text-slate-300 font-mono text-[11px] py-0.5">
                      <span className="text-sky-300 truncate">[[{r.title}]]</span>
                      <span className="text-[10px] text-slate-500">{r.tags?.join(' ') || ''}</span>
                    </div>
                  )) || <span className="text-slate-500 text-xs">No references indexed yet.</span>}
                </div>
              </div>

              {/* LAYER 4 */}
              <div className="p-5 rounded-2xl bg-[#10141f] border border-white/5 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-2">
                    <Terminal className="w-4 h-4" />
                    <span>Layer 4: Sessions & Dialogue</span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 font-mono">
                    {fiveLayers?.layer_4_sessions?.turn_count || 0} Active Turns
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-black/40 border border-white/5 text-xs space-y-1">
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                    <span>Logged Receipts:</span>
                    <span className="text-white font-semibold">{fiveLayers?.layer_4_sessions?.receipt_count || 0}</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                    <span>Estimated Context Tokens:</span>
                    <span className="text-cyan-400 font-semibold">{fiveLayers?.layer_4_sessions?.estimated_tokens || 0}</span>
                  </div>
                </div>
              </div>

              {/* LAYER 5 */}
              <div className="p-5 rounded-2xl bg-[#10141f] border border-white/5 space-y-3 md:col-span-2">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-2">
                    <Moon className="w-4 h-4" />
                    <span>Layer 5: Long-term Semantic Archive (ReMe / Dream Distillations)</span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 font-mono">
                    {fiveLayers?.layer_5_archive?.fact_count || 0} Facts Learned
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-black/40 border border-white/5 space-y-1">
                    <span className="text-[10px] text-slate-500 font-mono uppercase">Learned Memory Facts:</span>
                    <div className="space-y-1 max-h-28 overflow-y-auto mt-1">
                      {fiveLayers?.layer_5_archive?.facts?.map((f: any, i: number) => (
                        <div key={i} className="text-[11px] text-slate-300 font-mono">
                          <span className="text-purple-400 font-semibold">{f.key}:</span> {f.value}
                        </div>
                      )) || <span className="text-slate-500 text-xs">No facts stored yet.</span>}
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-black/40 border border-white/5 space-y-1">
                    <span className="text-[10px] text-slate-500 font-mono uppercase">Checkpoints & Reflections:</span>
                    <div className="space-y-1 max-h-28 overflow-y-auto mt-1">
                      {fiveLayers?.layer_5_archive?.checkpoints_and_reflections?.map((c: string, i: number) => (
                        <div key={i} className="text-[11px] text-slate-300 font-mono">
                          [[{c}]]
                        </div>
                      )) || <span className="text-slate-500 text-xs">No checkpoints recorded yet.</span>}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* AGENT REACH NATIVE INTERNET GATEWAY VIEW */}
        {activeTab === 'reach' && (
          <div className="flex-1 overflow-y-auto p-8 space-y-6">
            {/* Header & Doctor Banner */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/5 pb-6">
              <div>
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
                    <Globe className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                      Agent Reach Gateway
                      <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 font-mono font-normal">
                        Universal Internet Access
                      </span>
                    </h2>
                    <p className="text-xs text-slate-400">
                      Zero-config web extraction, free DuckDuckGo search, GitHub REST API, and developer community feeds.
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={runReachDoctor}
                  disabled={isDoctorRunning}
                  className="px-4 py-2 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 text-blue-300 text-xs font-semibold flex items-center gap-2 transition-all shadow-md shadow-blue-500/10 disabled:opacity-50 cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isDoctorRunning ? 'animate-spin' : ''}`} />
                  <span>{isDoctorRunning ? 'Diagnosing Channels...' : 'Run Channel Diagnostics'}</span>
                </button>
              </div>
            </div>

            {/* CHANNEL DOCTOR STATUS CARDS */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Jina Card */}
              <div className="p-4 rounded-2xl bg-[#0f1422] border border-white/5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-blue-400" />
                    Jina Reader
                  </span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-mono uppercase ${
                      reachDoctor?.channels?.jina_reader?.status === 'healthy'
                        ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-400'
                        : 'bg-amber-500/15 border border-amber-500/30 text-amber-400'
                    }`}
                  >
                    {reachDoctor?.channels?.jina_reader?.status || 'Active'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">
                  {reachDoctor?.channels?.jina_reader?.description || 'Zero-config markdown extraction via r.jina.ai'}
                </p>
                <div className="text-[10px] text-slate-500 font-mono">
                  Engine: <span className="text-blue-400">r.jina.ai + Scraper Fallback</span>
                </div>
              </div>

              {/* Web Search Card */}
              <div className="p-4 rounded-2xl bg-[#0f1422] border border-white/5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                    <Search className="w-3.5 h-3.5 text-cyan-400" />
                    DuckDuckGo Search
                  </span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-mono uppercase ${
                      reachDoctor?.channels?.web_search?.status === 'healthy'
                        ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-400'
                        : 'bg-cyan-500/15 border border-cyan-500/30 text-cyan-400'
                    }`}
                  >
                    {reachDoctor?.channels?.web_search?.status || 'Ready'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">
                  {reachDoctor?.channels?.web_search?.description || 'Free web search without requiring external API keys'}
                </p>
                <div className="text-[10px] text-slate-500 font-mono">
                  Engine: <span className="text-cyan-400">HTML & Instant Answers</span>
                </div>
              </div>

              {/* GitHub API Card */}
              <div className="p-4 rounded-2xl bg-[#0f1422] border border-white/5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                    <GitBranch className="w-3.5 h-3.5 text-purple-400" />
                    GitHub REST API
                  </span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-mono uppercase ${
                      reachDoctor?.channels?.github_api?.status === 'healthy'
                        ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-400'
                        : 'bg-purple-500/15 border border-purple-500/30 text-purple-400'
                    }`}
                  >
                    {reachDoctor?.channels?.github_api?.status || 'Connected'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">
                  {reachDoctor?.channels?.github_api?.description || 'Repository metadata, stats, and raw README reader'}
                </p>
                <div className="text-[10px] text-slate-500 font-mono">
                  Endpoint: <span className="text-purple-400">api.github.com</span>
                </div>
              </div>

              {/* Community Card */}
              <div className="p-4 rounded-2xl bg-[#0f1422] border border-white/5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                    <Radio className="w-3.5 h-3.5 text-amber-400" />
                    Developer Trends
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full font-mono uppercase bg-emerald-500/15 border border-emerald-500/30 text-emerald-400">
                    {reachDoctor?.channels?.community?.status || 'Live'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">
                  {reachDoctor?.channels?.community?.description || 'V2EX Hot Topics and Hacker News discussion feeds'}
                </p>
                <div className="text-[10px] text-slate-500 font-mono">
                  Feeds: <span className="text-amber-400">V2EX + Hacker News</span>
                </div>
              </div>
            </div>

            {/* REACH SUB-TABS */}
            <div className="flex items-center gap-2 border-b border-white/5 pb-2">
              <button
                onClick={() => setReachSubTab('fetcher')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer flex items-center gap-2 ${
                  reachSubTab === 'fetcher'
                    ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>Webpage to Markdown (Jina)</span>
              </button>

              <button
                onClick={() => setReachSubTab('search')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer flex items-center gap-2 ${
                  reachSubTab === 'search'
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <Search className="w-3.5 h-3.5" />
                <span>Multi-Engine Search</span>
              </button>

              <button
                onClick={() => setReachSubTab('github')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer flex items-center gap-2 ${
                  reachSubTab === 'github'
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <GitBranch className="w-3.5 h-3.5" />
                <span>GitHub Inspector</span>
              </button>

              <button
                onClick={() => {
                  setReachSubTab('community');
                  if (communityDiscussions.length === 0) {
                    handleCommunityReach(communitySource);
                  }
                }}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer flex items-center gap-2 ${
                  reachSubTab === 'community'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <Radio className="w-3.5 h-3.5" />
                <span>Trending Discussions</span>
              </button>
            </div>

            {/* TAB 1: WEBPAGE TO MARKDOWN (JINA) */}
            {reachSubTab === 'fetcher' && (
              <div className="space-y-4">
                <div className="p-5 rounded-2xl bg-[#0e1320] border border-white/5 space-y-3">
                  <div className="text-xs font-semibold text-blue-400 uppercase tracking-wider flex items-center gap-2">
                    <BookOpen className="w-4 h-4" />
                    <span>Jina Reader Web Fetcher</span>
                  </div>
                  <div className="flex flex-col md:flex-row gap-3">
                    <input
                      type="text"
                      value={fetchUrl}
                      onChange={(e) => setFetchUrl(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleFetchUrl()}
                      placeholder="Enter public URL (e.g. https://news.ycombinator.com or https://en.wikipedia.org/wiki/Artificial_intelligence)..."
                      className="flex-1 bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-blue-500 transition-colors font-mono"
                    />
                    <select
                      value={fetchMaxChars}
                      onChange={(e) => setFetchMaxChars(Number(e.target.value))}
                      className="bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-300 font-mono focus:outline-none"
                    >
                      <option value={5000}>Max 5,000 Chars</option>
                      <option value={10000}>Max 10,000 Chars</option>
                      <option value={20000}>Max 20,000 Chars</option>
                    </select>
                    <button
                      onClick={handleFetchUrl}
                      disabled={isFetchingUrl || !fetchUrl.trim()}
                      className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center justify-center gap-2 transition-all disabled:opacity-50 cursor-pointer shadow-md shadow-blue-600/20"
                    >
                      {isFetchingUrl ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Zap className="w-3.5 h-3.5" />
                      )}
                      <span>{isFetchingUrl ? 'Extracting Markdown...' : 'Fetch Markdown'}</span>
                    </button>
                  </div>
                </div>

                {fetchResult && (
                  <div className="p-5 rounded-2xl bg-[#0a0e1a] border border-blue-500/20 space-y-4">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-white/5 pb-3">
                      <div>
                        <h4 className="text-sm font-semibold text-white">
                          {fetchResult.title || fetchResult.url}
                        </h4>
                        <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400 mt-1">
                          <span>Engine: <span className="text-blue-400">{fetchResult.engine}</span></span>
                          <span>Length: <span className="text-cyan-400">{fetchResult.content?.length || 0} chars</span></span>
                          {fetchResult.truncated && (
                            <span className="text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                              Truncated ({fetchResult.total_chars} total)
                            </span>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => navigator.clipboard.writeText(fetchResult.content || '')}
                        className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-mono transition-all self-start md:self-auto cursor-pointer"
                      >
                        Copy Markdown
                      </button>
                    </div>

                    <pre className="p-4 rounded-xl bg-black/50 border border-white/5 text-xs font-mono text-slate-300 overflow-x-auto max-h-[500px] overflow-y-auto whitespace-pre-wrap leading-relaxed select-text">
                      {fetchResult.content}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: MULTI-ENGINE WEB SEARCH */}
            {reachSubTab === 'search' && (
              <div className="space-y-4">
                <div className="p-5 rounded-2xl bg-[#0e1320] border border-white/5 space-y-3">
                  <div className="text-xs font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
                    <Search className="w-4 h-4" />
                    <span>Multi-Engine Web Search (Free DuckDuckGo)</span>
                  </div>
                  <div className="flex gap-3">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleWebSearch()}
                      placeholder="Search anything across the public web (zero API keys)..."
                      className="flex-1 bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500 transition-colors font-mono"
                    />
                    <button
                      onClick={handleWebSearch}
                      disabled={isSearchingWeb || !searchQuery.trim()}
                      className="px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center gap-2 transition-all disabled:opacity-50 cursor-pointer shadow-md shadow-cyan-600/20"
                    >
                      {isSearchingWeb ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Search className="w-3.5 h-3.5" />
                      )}
                      <span>{isSearchingWeb ? 'Searching...' : 'Search'}</span>
                    </button>
                  </div>
                </div>

                {webSearchResults && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-xs text-slate-400 font-mono px-1">
                      <span>Query: "{webSearchResults.query}"</span>
                      <span>Found {webSearchResults.results?.length || 0} results ({webSearchResults.engine})</span>
                    </div>

                    <div className="grid grid-cols-1 gap-3">
                      {webSearchResults.results?.map((item: any, idx: number) => (
                        <div
                          key={idx}
                          className="p-4 rounded-xl bg-[#0e1320] border border-white/5 hover:border-cyan-500/30 transition-all space-y-2 group"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <a
                              href={item.url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-sm font-semibold text-cyan-400 group-hover:text-cyan-300 transition-colors flex items-center gap-1.5"
                            >
                              <span>{item.title}</span>
                              <ExternalLink className="w-3.5 h-3.5 opacity-60 group-hover:opacity-100" />
                            </a>
                            <span className="text-[10px] text-slate-500 font-mono truncate max-w-[200px]">
                              {item.url}
                            </span>
                          </div>
                          <p className="text-xs text-slate-300 leading-relaxed">
                            {item.snippet}
                          </p>
                          <div className="flex items-center gap-3 pt-1">
                            <button
                              onClick={() => {
                                setFetchUrl(item.url);
                                setReachSubTab('fetcher');
                              }}
                              className="text-[11px] text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1 cursor-pointer"
                            >
                              <span>Read via Jina Markdown</span>
                              <ChevronRight className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: GITHUB INSPECTOR */}
            {reachSubTab === 'github' && (
              <div className="space-y-4">
                <div className="p-5 rounded-2xl bg-[#0e1320] border border-white/5 space-y-3">
                  <div className="text-xs font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-2">
                    <GitBranch className="w-4 h-4" />
                    <span>GitHub Repository & Release Inspector</span>
                  </div>
                  <div className="flex flex-col md:flex-row gap-3">
                    <input
                      type="text"
                      value={githubRepo}
                      onChange={(e) => setGithubRepo(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleGithubReach()}
                      placeholder="e.g. Panniantong/Agent-Reach, NousResearch/hermes-agent, or Trycua/cua..."
                      className="flex-1 bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-purple-500 transition-colors font-mono"
                    />
                    <div className="flex rounded-xl bg-black/40 p-1 border border-white/10">
                      <button
                        onClick={() => setGithubAction('info')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                          githubAction === 'info'
                            ? 'bg-purple-600 text-white'
                            : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        Metadata
                      </button>
                      <button
                        onClick={() => setGithubAction('readme')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                          githubAction === 'readme'
                            ? 'bg-purple-600 text-white'
                            : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        README
                      </button>
                    </div>
                    <button
                      onClick={handleGithubReach}
                      disabled={isFetchingGithub || !githubRepo.trim()}
                      className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center gap-2 transition-all disabled:opacity-50 cursor-pointer shadow-md shadow-purple-600/20"
                    >
                      {isFetchingGithub ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <GitBranch className="w-3.5 h-3.5" />
                      )}
                      <span>{isFetchingGithub ? 'Querying GitHub...' : 'Inspect Repo'}</span>
                    </button>
                  </div>
                </div>

                {githubResult && (
                  <div className="p-5 rounded-2xl bg-[#0a0e1a] border border-purple-500/20 space-y-4">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-white/5 pb-4">
                      <div>
                        <h4 className="text-base font-bold text-white flex items-center gap-2">
                          <span>{githubResult.full_name || githubResult.repo}</span>
                          <a
                            href={githubResult.html_url || `https://github.com/${githubResult.repo}`}
                            target="_blank"
                            rel="noreferrer"
                            className="text-slate-400 hover:text-white"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        </h4>
                        <p className="text-xs text-slate-300 mt-1 max-w-2xl">
                          {githubResult.description || 'No description provided.'}
                        </p>
                      </div>

                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 font-mono">
                          <Star className="w-3.5 h-3.5" />
                          <span>{githubResult.stars?.toLocaleString() || 0}</span>
                        </span>
                        <span className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-300 font-mono">
                          <GitBranch className="w-3.5 h-3.5" />
                          <span>{githubResult.forks?.toLocaleString() || 0}</span>
                        </span>
                        {githubResult.language && (
                          <span className="text-xs px-2.5 py-1 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-300 font-mono">
                            {githubResult.language}
                          </span>
                        )}
                        {githubResult.license && (
                          <span className="text-xs px-2.5 py-1 rounded-lg bg-slate-800 border border-white/10 text-slate-300 font-mono">
                            {githubResult.license}
                          </span>
                        )}
                      </div>
                    </div>

                    {githubResult.readme ? (
                      <div className="space-y-2">
                        <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider font-mono">
                          Raw README Preview:
                        </span>
                        <pre className="p-4 rounded-xl bg-black/50 border border-white/5 text-xs font-mono text-slate-300 overflow-x-auto max-h-[500px] overflow-y-auto whitespace-pre-wrap leading-relaxed select-text">
                          {githubResult.readme}
                        </pre>
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
                        <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                          <span className="text-slate-500 text-[10px] block">OPEN ISSUES</span>
                          <span className="text-white font-semibold text-sm">{githubResult.open_issues || 0}</span>
                        </div>
                        <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                          <span className="text-slate-500 text-[10px] block">LANGUAGE</span>
                          <span className="text-white font-semibold text-sm">{githubResult.language || 'N/A'}</span>
                        </div>
                        <div className="p-3 rounded-xl bg-black/40 border border-white/5 col-span-2">
                          <span className="text-slate-500 text-[10px] block">LAST UPDATED</span>
                          <span className="text-white font-semibold text-xs">{githubResult.updated_at || 'Recent'}</span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* TAB 4: TRENDING DEVELOPER DISCUSSIONS */}
            {reachSubTab === 'community' && (
              <div className="space-y-4">
                <div className="p-5 rounded-2xl bg-[#0e1320] border border-white/5 space-y-3">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-2">
                      <Radio className="w-4 h-4" />
                      <span>Developer Community Trends & Hot Topics</span>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="flex rounded-xl bg-black/40 p-1 border border-white/10">
                        <button
                          onClick={() => {
                            setCommunitySource('v2ex');
                            handleCommunityReach('v2ex');
                          }}
                          className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                            communitySource === 'v2ex'
                              ? 'bg-amber-600 text-white'
                              : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          V2EX Hot Topics
                        </button>
                        <button
                          onClick={() => {
                            setCommunitySource('hackernews');
                            handleCommunityReach('hackernews');
                          }}
                          className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                            communitySource === 'hackernews'
                              ? 'bg-amber-600 text-white'
                              : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          Hacker News
                        </button>
                      </div>

                      <button
                        onClick={() => handleCommunityReach(communitySource)}
                        disabled={isFetchingCommunity}
                        className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-medium flex items-center gap-1.5 transition-all cursor-pointer"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 ${isFetchingCommunity ? 'animate-spin' : ''}`} />
                        <span>Refresh</span>
                      </button>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {communityDiscussions.map((disc: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl bg-[#0e1320] border border-white/5 hover:border-amber-500/30 transition-all space-y-2 flex flex-col justify-between"
                    >
                      <div className="space-y-1">
                        <div className="flex items-start justify-between gap-2">
                          <a
                            href={disc.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs font-semibold text-slate-100 hover:text-amber-300 transition-colors line-clamp-2"
                          >
                            {disc.title}
                          </a>
                          <ExternalLink className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
                        </div>
                        {disc.content && (
                          <p className="text-[11px] text-slate-400 line-clamp-2">
                            {disc.content}
                          </p>
                        )}
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-white/5 text-[10px] font-mono text-slate-500">
                        <div className="flex items-center gap-2">
                          {disc.author && <span>By: <span className="text-amber-400">{disc.author}</span></span>}
                          {disc.by && <span>By: <span className="text-amber-400">{disc.by}</span></span>}
                          {disc.node && (
                            <span className="px-1.5 py-0.5 rounded bg-white/5 text-slate-400">
                              {disc.node}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {disc.score !== undefined && (
                            <span className="text-amber-400">{disc.score} pts</span>
                          )}
                          <span>{disc.replies !== undefined ? `${disc.replies} replies` : `${disc.comments || 0} comments`}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* PHASE 11: LOBEHUB CHIEF AGENT OPERATOR & MULTI-AGENT COLLABORATION TAB   */}
        {/* ========================================================================= */}
        {activeTab === 'operator' && (
          <div className="flex-1 flex flex-col h-[calc(100vh-3.5rem)] overflow-y-auto p-6 space-y-6">
            {/* OPERATOR HEADER & CONTROLS */}
            <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-black/40 border border-indigo-500/20 shadow-xl space-y-4">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                      <Users className="w-5 h-5" />
                    </div>
                    <div>
                      <h2 className="text-base font-bold text-white tracking-wide flex items-center gap-2">
                        <span>Chief Agent Operator & Collaboration Groups</span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 font-mono">
                          LobeHub Spec
                        </span>
                      </h2>
                      <p className="text-xs text-slate-400 mt-0.5">
                        7x24 Autonomous Operations, Team Roster Governance, and Multi-Agent Collaboration Groups.
                      </p>
                    </div>
                  </div>
                </div>

                {/* STATUS & METRICS PILLS */}
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-mono flex items-center gap-1.5">
                    <Briefcase className="w-3.5 h-3.5" />
                    <span>{teamMembers.length} Agents Hired</span>
                  </span>
                  <span className="text-xs px-2.5 py-1 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-300 font-mono flex items-center gap-1.5">
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>{operatorGroups.length} Agent Groups</span>
                  </span>
                  <span className="text-xs px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-mono flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{shiftReports.length} Shifts Executed</span>
                  </span>
                  <span className="text-xs px-2.5 py-1 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-mono flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span>7x24 Active</span>
                  </span>
                </div>
              </div>

              {/* SUB-TABS & ACTIONS BAR */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-white/5">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setOperatorSubTab('roster')}
                    className={`px-3 py-1.5 rounded-xl text-xs font-medium flex items-center gap-2 transition-all cursor-pointer ${
                      operatorSubTab === 'roster'
                        ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                        : 'bg-white/5 text-slate-400 hover:text-white hover:bg-white/10'
                    }`}
                  >
                    <Users className="w-3.5 h-3.5" />
                    <span>Team Roster ({teamMembers.length})</span>
                  </button>

                  <button
                    onClick={() => setOperatorSubTab('groups')}
                    className={`px-3 py-1.5 rounded-xl text-xs font-medium flex items-center gap-2 transition-all cursor-pointer ${
                      operatorSubTab === 'groups'
                        ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                        : 'bg-white/5 text-slate-400 hover:text-white hover:bg-white/10'
                    }`}
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>Agent Groups ({operatorGroups.length})</span>
                  </button>

                  <button
                    onClick={() => setOperatorSubTab('shifts')}
                    className={`px-3 py-1.5 rounded-xl text-xs font-medium flex items-center gap-2 transition-all cursor-pointer ${
                      operatorSubTab === 'shifts'
                        ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                        : 'bg-white/5 text-slate-400 hover:text-white hover:bg-white/10'
                    }`}
                  >
                    <Clock className="w-3.5 h-3.5" />
                    <span>Autonomous Shifts ({shiftReports.length})</span>
                  </button>
                </div>

                <div className="flex items-center gap-2">
                  {operatorSubTab === 'roster' && (
                    <button
                      onClick={() => setShowHireModal(!showHireModal)}
                      className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-medium flex items-center gap-1.5 shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
                    >
                      <UserPlus className="w-3.5 h-3.5" />
                      <span>{showHireModal ? 'Close Form' : 'Hire Teammate'}</span>
                    </button>
                  )}
                  {operatorSubTab === 'groups' && (
                    <button
                      onClick={() => setShowCreateGroupModal(!showCreateGroupModal)}
                      className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-medium flex items-center gap-1.5 shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>{showCreateGroupModal ? 'Close Form' : 'New Group'}</span>
                    </button>
                  )}
                  <button
                    onClick={() => {
                      fetchTeamMembers();
                      fetchOperatorGroups();
                      fetchShiftReports();
                    }}
                    className="p-1.5 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 transition-all cursor-pointer"
                    title="Refresh Operator Data"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isLoadingTeam ? 'animate-spin' : ''}`} />
                  </button>
                </div>
              </div>
            </div>

            {/* ===================================================================== */}
            {/* SUB-TAB 1: TEAM ROSTER                                                */}
            {/* ===================================================================== */}
            {operatorSubTab === 'roster' && (
              <div className="space-y-6">
                {/* HIRE AGENT INLINE FORM */}
                {showHireModal && (
                  <div className="p-6 rounded-2xl bg-[#0e1320] border border-indigo-500/30 shadow-2xl space-y-4">
                    <div className="flex items-center justify-between border-b border-white/5 pb-3">
                      <div className="flex items-center gap-2">
                        <UserPlus className="w-4 h-4 text-indigo-400" />
                        <h3 className="text-sm font-semibold text-white">Hire Specialized Agent Teammate</h3>
                      </div>
                      <span className="text-[11px] text-slate-400 font-mono">MaxIM AI Staff Roster</span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-1.5">
                        <label className="text-xs font-medium text-slate-300">Agent Display Name</label>
                        <input
                          type="text"
                          placeholder="e.g. Security Sentinel"
                          value={hireName}
                          onChange={(e) => setHireName(e.target.value)}
                          className="w-full px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      <div className="space-y-1.5">
                        <label className="text-xs font-medium text-slate-300">Specialty Role / Function</label>
                        <input
                          type="text"
                          placeholder="e.g. AppSec & Threat Modeling Auditor"
                          value={hireRole}
                          onChange={(e) => setHireRole(e.target.value)}
                          className="w-full px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      <div className="space-y-1.5 md:col-span-2">
                        <label className="text-xs font-medium text-slate-300">Operating Persona & Core Directives</label>
                        <textarea
                          rows={2}
                          placeholder="e.g. Zero-trust security reviewer. Audits credential hygiene, input sanitization, and threat vectors."
                          value={hirePersona}
                          onChange={(e) => setHirePersona(e.target.value)}
                          className="w-full px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      <div className="space-y-1.5">
                        <label className="text-xs font-medium text-slate-300">Avatar Icon</label>
                        <select
                          value={hireAvatar}
                          onChange={(e) => setHireAvatar(e.target.value)}
                          className="w-full px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white focus:outline-none focus:border-indigo-500"
                        >
                          <option value="Sparkles">Sparkles (General / Chief)</option>
                          <option value="BookOpen">BookOpen (Obsidian Knowledge)</option>
                          <option value="Globe">Globe (Internet / Web Reach)</option>
                          <option value="Zap">Zap (Critic / Auditor)</option>
                          <option value="Database">Database (Memory / Storage)</option>
                          <option value="Shield">Shield (Security / Guardian)</option>
                          <option value="Cpu">Cpu (Deep Architecture)</option>
                        </select>
                      </div>

                      <div className="space-y-1.5">
                        <label className="text-xs font-medium text-slate-300">Authorized Toolsets</label>
                        <div className="flex flex-wrap gap-2 pt-1">
                          {['vault', 'reach', 'memory', 'perception', 'cua'].map((ts) => (
                            <button
                              key={ts}
                              type="button"
                              onClick={() => {
                                if (hireToolsets.includes(ts)) {
                                  setHireToolsets(hireToolsets.filter((t) => t !== ts));
                                } else {
                                  setHireToolsets([...hireToolsets, ts]);
                                }
                              }}
                              className={`px-2.5 py-1 rounded-lg text-[11px] font-mono transition-all cursor-pointer ${
                                hireToolsets.includes(ts)
                                  ? 'bg-indigo-600 text-white border border-indigo-400'
                                  : 'bg-black/40 text-slate-400 border border-white/10 hover:text-white'
                              }`}
                            >
                              {ts}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-end gap-2 pt-3 border-t border-white/5">
                      <button
                        onClick={() => setShowHireModal(false)}
                        className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-medium transition-all cursor-pointer"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleHireAgent}
                        className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all cursor-pointer"
                      >
                        Confirm Hire
                      </button>
                    </div>
                  </div>
                )}

                {/* TEAM GRID */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {teamMembers.map((member) => (
                    <div
                      key={member.id}
                      className="p-5 rounded-2xl bg-[#0e1320] border border-white/5 hover:border-indigo-500/30 transition-all flex flex-col justify-between space-y-4 shadow-lg"
                    >
                      <div className="space-y-3">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-300 font-bold text-sm">
                              {member.avatar === 'Globe' ? (
                                <Globe className="w-5 h-5 text-blue-400" />
                              ) : member.avatar === 'BookOpen' ? (
                                <BookOpen className="w-5 h-5 text-emerald-400" />
                              ) : member.avatar === 'Zap' ? (
                                <Zap className="w-5 h-5 text-amber-400" />
                              ) : member.avatar === 'Database' ? (
                                <Database className="w-5 h-5 text-purple-400" />
                              ) : member.avatar === 'Shield' ? (
                                <Shield className="w-5 h-5 text-rose-400" />
                              ) : (
                                <Sparkles className="w-5 h-5 text-indigo-400" />
                              )}
                            </div>
                            <div>
                              <h4 className="text-sm font-semibold text-white leading-tight">{member.name}</h4>
                              <span className="text-[11px] text-indigo-300 font-mono block mt-0.5">
                                {member.role}
                              </span>
                            </div>
                          </div>

                          <span
                            className={`flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                              member.status === 'active'
                                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                                : 'bg-slate-800/60 border-white/10 text-slate-400'
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                member.status === 'active' ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'
                              }`}
                            />
                            <span>{member.status}</span>
                          </span>
                        </div>

                        <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed italic font-sans">
                          "{member.persona}"
                        </p>
                      </div>

                      <div className="space-y-3 pt-3 border-t border-white/5">
                        <div className="flex items-center justify-between text-[11px] font-mono">
                          <span className="text-slate-500">TOOLSETS</span>
                          <div className="flex flex-wrap gap-1">
                            {member.toolsets.map((ts) => (
                              <span
                                key={ts}
                                className="px-1.5 py-0.5 rounded bg-white/5 border border-white/5 text-[10px] text-slate-300"
                              >
                                {ts}
                              </span>
                            ))}
                          </div>
                        </div>

                        <div className="flex items-center justify-between text-[11px] font-mono">
                          <span className="text-slate-500">COMPLETED TASKS</span>
                          <span className="text-indigo-300 font-semibold">{member.total_tasks} missions</span>
                        </div>

                        <div className="flex items-center gap-2 pt-1">
                          <button
                            onClick={() => {
                              setSelectedShiftAgentId(member.id);
                              setOperatorSubTab('shifts');
                            }}
                            className="flex-1 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 text-indigo-300 text-xs font-medium flex items-center justify-center gap-1.5 transition-all cursor-pointer"
                          >
                            <Play className="w-3 h-3" />
                            <span>Dispatch Shift</span>
                          </button>

                          {!member.id.startsWith('agent_chief') && (
                            <button
                              onClick={() => handleFireAgent(member.id)}
                              className="p-1.5 rounded-xl bg-white/5 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 border border-white/5 hover:border-rose-500/30 transition-all cursor-pointer"
                              title="Dismiss Agent Teammate"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ===================================================================== */}
            {/* SUB-TAB 2: MULTI-AGENT COLLABORATION GROUPS                           */}
            {/* ===================================================================== */}
            {operatorSubTab === 'groups' && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1">
                {/* LEFT: GROUP ROSTER */}
                <div className="space-y-4">
                  {/* CREATE GROUP FORM */}
                  {showCreateGroupModal && (
                    <div className="p-4 rounded-2xl bg-[#0e1320] border border-indigo-500/30 space-y-3">
                      <div className="flex items-center justify-between border-b border-white/5 pb-2">
                        <span className="text-xs font-semibold text-white">Create Collaboration Group</span>
                      </div>
                      <input
                        type="text"
                        placeholder="Group Name (e.g. Architecture Council)"
                        value={newGroupName}
                        onChange={(e) => setNewGroupName(e.target.value)}
                        className="w-full px-3 py-1.5 rounded-xl bg-black/40 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                      />
                      <input
                        type="text"
                        placeholder="Charter / Purpose Description"
                        value={newGroupDesc}
                        onChange={(e) => setNewGroupDesc(e.target.value)}
                        className="w-full px-3 py-1.5 rounded-xl bg-black/40 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                      />
                      <input
                        type="text"
                        placeholder="Active Topic (Optional)"
                        value={newGroupTopic}
                        onChange={(e) => setNewGroupTopic(e.target.value)}
                        className="w-full px-3 py-1.5 rounded-xl bg-black/40 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                      />
                      <div className="space-y-1">
                        <span className="text-[10px] text-slate-400 uppercase font-mono">Select Members</span>
                        <div className="flex flex-wrap gap-1.5">
                          {teamMembers.map((m) => (
                            <button
                              key={m.id}
                              type="button"
                              onClick={() => {
                                if (newGroupMembers.includes(m.id)) {
                                  setNewGroupMembers(newGroupMembers.filter((id) => id !== m.id));
                                } else {
                                  setNewGroupMembers([...newGroupMembers, m.id]);
                                }
                              }}
                              className={`px-2 py-0.5 rounded text-[10px] font-mono transition-all ${
                                newGroupMembers.includes(m.id)
                                  ? 'bg-indigo-600 text-white'
                                  : 'bg-black/40 text-slate-400 border border-white/10'
                              }`}
                            >
                              {m.name.split(' ')[0]}
                            </button>
                          ))}
                        </div>
                      </div>
                      <div className="flex justify-end gap-2 pt-2">
                        <button
                          onClick={() => setShowCreateGroupModal(false)}
                          className="px-3 py-1 rounded-lg bg-white/5 text-slate-400 text-xs"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleCreateGroup}
                          className="px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
                        >
                          Create
                        </button>
                      </div>
                    </div>
                  )}

                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono">
                      Active Collaboration Groups
                    </span>
                    <div className="space-y-2">
                      {operatorGroups.map((grp) => (
                        <div
                          key={grp.id}
                          onClick={() => {
                            setSelectedGroupId(grp.id);
                            fetchGroupMessages(grp.id);
                          }}
                          className={`p-4 rounded-xl cursor-pointer transition-all border ${
                            selectedGroupId === grp.id
                              ? 'bg-indigo-950/30 border-indigo-500/50 shadow-md shadow-indigo-500/10'
                              : 'bg-[#0e1320] border-white/5 hover:border-white/10 hover:bg-white/[0.02]'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <h4 className="text-xs font-bold text-white tracking-wide">{grp.name}</h4>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/5 text-slate-400">
                              {grp.member_ids.length} agents
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 line-clamp-2 mt-1 leading-snug">
                            {grp.description}
                          </p>
                          {grp.topic && (
                            <span className="inline-block mt-2 text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/20 text-indigo-300">
                              Topic: {grp.topic}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* RIGHT: CHAT FEED & MULTI-AGENT ROUND DISPATCHER */}
                <div className="lg:col-span-2 flex flex-col h-[650px] rounded-2xl bg-[#0e1320] border border-white/5 overflow-hidden">
                  {/* GROUP HEADER */}
                  {selectedGroupId && (
                    <div className="p-4 border-b border-white/5 bg-[#0a0d14]/70 flex items-center justify-between gap-3">
                      <div>
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                          <Users className="w-4 h-4 text-indigo-400" />
                          <span>{operatorGroups.find((g) => g.id === selectedGroupId)?.name || 'Collaboration Group'}</span>
                        </h3>
                        <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">
                          {operatorGroups.find((g) => g.id === selectedGroupId)?.description}
                        </p>
                      </div>

                      <div className="flex items-center gap-1.5">
                        {operatorGroups
                          .find((g) => g.id === selectedGroupId)
                          ?.member_ids.map((mId) => {
                            const agent = teamMembers.find((m) => m.id === mId);
                            return (
                              <span
                                key={mId}
                                className="px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-[10px] font-mono"
                                title={agent?.role}
                              >
                                {agent ? agent.name.split(' ')[0] : mId}
                              </span>
                            );
                          })}
                      </div>
                    </div>
                  )}

                  {/* MESSAGES FEED */}
                  <div className="flex-1 p-4 overflow-y-auto space-y-3">
                    {isLoadingGroupMessages ? (
                      <div className="h-full flex flex-col items-center justify-center p-8 space-y-2">
                        <RefreshCw className="w-5 h-5 text-indigo-400 animate-spin" />
                        <span className="text-xs text-slate-400 font-mono">Loading council deliberation history...</span>
                      </div>
                    ) : groupMessages.length === 0 ? (
                      <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-3">
                        <MessageSquare className="w-10 h-10 text-indigo-400/40" />
                        <h4 className="text-xs font-semibold text-slate-300">No Messages in this Group Yet</h4>
                        <p className="text-[11px] text-slate-500 max-w-sm">
                          Dispatch an objective, question, or proposition below to have all assigned member agents co-reason, critique, and synthesize sequentially.
                        </p>
                      </div>
                    ) : (
                      groupMessages.map((msg, idx) => (
                        <div
                          key={idx}
                          className={`p-3.5 rounded-xl border leading-relaxed space-y-1.5 ${
                            msg.sender_id === 'user'
                              ? 'bg-blue-950/20 border-blue-500/20 ml-6 text-slate-200'
                              : 'bg-black/30 border-white/5 mr-6 text-slate-300'
                          }`}
                        >
                          <div className="flex items-center justify-between text-[11px] font-mono">
                            <div className="flex items-center gap-2">
                              <span
                                className={`font-semibold ${
                                  msg.sender_id === 'user' ? 'text-blue-400' : 'text-indigo-400'
                                }`}
                              >
                                {msg.sender_name}
                              </span>
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-white/5 text-slate-400">
                                {msg.role}
                              </span>
                            </div>
                            <span className="text-[10px] text-slate-500">
                              {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                          <p className="text-xs font-sans whitespace-pre-wrap select-text">{msg.content}</p>
                        </div>
                      ))
                    )}
                    {isGroupChatting && (
                      <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/30 flex items-center gap-3 animate-pulse">
                        <RefreshCw className="w-4 h-4 text-indigo-400 animate-spin" />
                        <span className="text-xs text-indigo-300 font-mono">
                          Council agents are deliberating round-robin...
                        </span>
                      </div>
                    )}
                  </div>

                  {/* BOTTOM PROMPT INPUT BAR */}
                  <div className="p-3 border-t border-white/5 bg-[#0a0d14]/90 space-y-2">
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        placeholder="Pose a mission, question, or proposition to the council..."
                        value={groupChatPrompt}
                        onChange={(e) => setGroupChatPrompt(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && !isGroupChatting && handleRunGroupChat()}
                        className="flex-1 px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                      />
                      <div className="flex items-center gap-1.5">
                        <select
                          value={groupRounds}
                          onChange={(e) => setGroupRounds(Number(e.target.value))}
                          className="px-2 py-2 rounded-xl bg-black/40 border border-white/10 text-[11px] font-mono text-slate-300 focus:outline-none focus:border-indigo-500"
                          title="Discussion Rounds"
                        >
                          <option value={1}>1 Round</option>
                          <option value={2}>2 Rounds</option>
                        </select>

                        <button
                          onClick={handleRunGroupChat}
                          disabled={isGroupChatting || !groupChatPrompt.trim()}
                          className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md shadow-indigo-600/30 cursor-pointer"
                        >
                          <Send className="w-3.5 h-3.5" />
                          <span>Dispatch</span>
                        </button>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 overflow-x-auto pb-1">
                      <span className="text-[10px] text-slate-500 font-mono shrink-0">SUGGESTIONS:</span>
                      <button
                        onClick={() => setGroupChatPrompt('Review codebase boundaries, zero-trust security, and memory safeguards.')}
                        className="px-2 py-0.5 rounded bg-white/5 hover:bg-white/10 text-[10px] text-slate-400 font-mono whitespace-nowrap cursor-pointer"
                      >
                        Audit Security & Memory
                      </button>
                      <button
                        onClick={() => setGroupChatPrompt('Synthesize cross-note knowledge relationships in the Obsidian vault.')}
                        className="px-2 py-0.5 rounded bg-white/5 hover:bg-white/10 text-[10px] text-slate-400 font-mono whitespace-nowrap cursor-pointer"
                      >
                        Synthesize Vault
                      </button>
                      <button
                        onClick={() => setGroupChatPrompt('Evaluate latest open-source agent patterns and propose next integration.')}
                        className="px-2 py-0.5 rounded bg-white/5 hover:bg-white/10 text-[10px] text-slate-400 font-mono whitespace-nowrap cursor-pointer"
                      >
                        Scout Emerging Patterns
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ===================================================================== */}
            {/* SUB-TAB 3: AUTONOMOUS SHIFTS & REPORTS                                */}
            {/* ===================================================================== */}
            {operatorSubTab === 'shifts' && (
              <div className="space-y-6">
                {/* SHIFT DISPATCHER CARD */}
                <div className="p-6 rounded-2xl bg-[#0e1320] border border-white/5 shadow-xl space-y-4">
                  <div className="flex items-center justify-between border-b border-white/5 pb-3">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-emerald-400" />
                      <h3 className="text-sm font-semibold text-white">Dispatch Autonomous Agent Shift</h3>
                    </div>
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                      Auto-logs into Obsidian Vault (03 - Agents)
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-slate-300">Target Agent Teammate</label>
                      <select
                        value={selectedShiftAgentId}
                        onChange={(e) => setSelectedShiftAgentId(e.target.value)}
                        className="w-full px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white focus:outline-none focus:border-indigo-500"
                      >
                        {teamMembers.map((m) => (
                          <option key={m.id} value={m.id}>
                            {m.name} ({m.role})
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="space-y-1.5 md:col-span-2">
                      <label className="text-xs font-medium text-slate-300">Shift Mission / Objective</label>
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={shiftTaskInput}
                          onChange={(e) => setShiftTaskInput(e.target.value)}
                          placeholder="e.g. Audit codebase boundaries, verify receipts, and generate an executive report."
                          className="flex-1 px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                        />
                        <button
                          onClick={handleExecuteShift}
                          disabled={isExecutingShift || !shiftTaskInput.trim()}
                          className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-emerald-600/30 transition-all cursor-pointer whitespace-nowrap"
                        >
                          <Play className={`w-3.5 h-3.5 ${isExecutingShift ? 'animate-spin' : ''}`} />
                          <span>{isExecutingShift ? 'Executing Shift...' : 'Launch Shift'}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* TIMELINE OF REPORTS */}
                <div className="space-y-3">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono">
                    Recent Executive Shift Reports ({shiftReports.length})
                  </span>

                  {shiftReports.length === 0 ? (
                    <div className="p-8 rounded-2xl bg-[#0e1320] border border-white/5 text-center text-slate-500 text-xs">
                      No shift reports generated yet. Launch a shift mission above to create the first executive report.
                    </div>
                  ) : (
                    shiftReports.map((report) => (
                      <div
                        key={report.id}
                        className="p-5 rounded-2xl bg-[#0e1320] border border-white/5 hover:border-emerald-500/30 transition-all space-y-3 shadow-md"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2.5">
                            <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                              <CheckCircle2 className="w-4 h-4" />
                            </div>
                            <div>
                              <h4 className="text-xs font-bold text-white tracking-wide">{report.agent_name}</h4>
                              <span className="text-[10px] font-mono text-slate-400">
                                Mission: {report.task}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
                              {report.status}
                            </span>
                            <span className="text-[10px] font-mono text-slate-500">
                              {new Date(report.timestamp).toLocaleString()}
                            </span>
                          </div>
                        </div>

                        <div className="p-4 rounded-xl bg-black/40 border border-white/5 space-y-1">
                          <span className="text-[10px] font-semibold text-indigo-400 uppercase tracking-wider font-mono">
                            Executive Synthesis:
                          </span>
                          <p className="text-xs text-slate-300 font-sans leading-relaxed whitespace-pre-wrap select-text">
                            {report.summary}
                          </p>
                        </div>

                        <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pt-1 border-t border-white/5">
                          <span className="flex items-center gap-1 text-purple-400">
                            <BookOpen className="w-3 h-3" />
                            <span>Vault Note Created in [[03 - Agents]]</span>
                          </span>
                          <span>Report ID: {report.id}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* OVERNIGHT & IDLE INTELLIGENCE SCOUT TAB */}
        {activeTab === 'scout' && (
          <div className="flex-1 overflow-y-auto p-8 max-w-6xl mx-auto space-y-8 font-sans">
            {/* SCOUT HEADER */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/5 pb-6">
              <div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-300">
                    <Newspaper className="w-4 h-4" />
                  </div>
                  <h1 className="text-xl font-bold text-white tracking-wide">
                    Overnight & Idle Intelligence Scout
                  </h1>
                </div>
                <p className="text-xs text-slate-400 mt-1 max-w-2xl">
                  Autonomous night & idle web research scouring news, breakthroughs, and ideas aligned with your habits & TELOS.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2.5">
                <div className="px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-[11px] font-mono flex items-center gap-1.5 text-slate-300">
                  <Moon className="w-3.5 h-3.5 text-amber-400" />
                  <span>Sleep Window: {scoutStatus.is_night ? '🌙 Active' : '23:00 - 07:00'}</span>
                </div>
                <div className="px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-[11px] font-mono flex items-center gap-1.5 text-slate-300">
                  <Clock className="w-3.5 h-3.5 text-cyan-400" />
                  <span>{scoutStatus.minutes_idle}m Inactive</span>
                </div>
                <button
                  onClick={() => handleTriggerScoutCycle('manual')}
                  disabled={isTriggeringScout}
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-amber-500/25 transition-all cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isTriggeringScout ? 'animate-spin' : ''}`} />
                  <span>{isTriggeringScout ? 'Scouting Live Web...' : 'Run Overnight Scout Now'}</span>
                </button>
              </div>
            </div>

            {/* MAIN 2-COLUMN VIEW */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* LEFT 2 COLUMNS: LATEST BRIEFING (HERO CARD) */}
              <div className="lg:col-span-2 space-y-6">
                {scoutLatestReport ? (
                  <div className="p-6 rounded-2xl bg-[#0e1320] border border-amber-500/20 shadow-xl space-y-5">
                    <div className="flex flex-wrap items-center justify-between gap-2 pb-4 border-b border-white/5">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/25">
                            {scoutLatestReport.trigger_type.toUpperCase()} SCOUT
                          </span>
                          <span className="text-[11px] font-mono text-slate-500">
                            {new Date(scoutLatestReport.created_at).toLocaleString()}
                          </span>
                        </div>
                        <h2 className="text-base font-bold text-white tracking-wide">
                          {scoutLatestReport.title}
                        </h2>
                      </div>

                      <button
                        onClick={() => handlePlayVoice(`scout_${scoutLatestReport.id}`, scoutLatestReport.audio_brief)}
                        className="px-3 py-1.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-200 text-xs font-mono flex items-center gap-1.5 transition-all cursor-pointer shadow-md shadow-amber-950/20"
                      >
                        {audioPlaying === `scout_${scoutLatestReport.id}` ? (
                          <>
                            <VolumeX className="w-3.5 h-3.5 text-amber-300 animate-pulse" />
                            <span>Stop Voice</span>
                          </>
                        ) : (
                          <>
                            <Volume2 className="w-3.5 h-3.5 text-amber-300" />
                            <span>Play Spoken Brief</span>
                          </>
                        )}
                      </button>
                    </div>

                    {/* TOPICS TAGS */}
                    <div className="flex flex-wrap gap-1.5">
                      {scoutLatestReport.topics.map((top, idx) => (
                        <span
                          key={idx}
                          className="px-2.5 py-1 rounded-lg bg-white/5 border border-white/5 text-[11px] font-mono text-amber-200/90"
                        >
                          #{top}
                        </span>
                      ))}
                    </div>

                    {/* SPOKEN AUDIO SUMMARY CARD */}
                    {scoutLatestReport.audio_brief && (
                      <div className="p-4 rounded-xl bg-gradient-to-r from-amber-950/40 via-[#141b2c] to-black/40 border border-amber-500/20 space-y-1.5">
                        <span className="text-[10px] font-mono uppercase tracking-wider text-amber-400 font-semibold flex items-center gap-1.5">
                          <Volume2 className="w-3.5 h-3.5" /> Spoken Morning Audio Brief
                        </span>
                        <p className="text-xs text-amber-100/90 font-sans italic leading-relaxed">
                          "{scoutLatestReport.audio_brief}"
                        </p>
                      </div>
                    )}

                    {/* EXECUTIVE SUMMARY */}
                    <div className="p-4 rounded-xl bg-black/40 border border-white/5 space-y-1.5">
                      <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
                        Executive Overview
                      </span>
                      <p className="text-xs text-slate-200 leading-relaxed font-sans">
                        {scoutLatestReport.summary}
                      </p>
                    </div>

                    {/* STRUCTURED BRIEFING MARKDOWN PREVIEW */}
                    <div className="p-4 rounded-xl bg-black/60 border border-white/5 space-y-3 max-h-96 overflow-y-auto text-xs text-slate-300 leading-relaxed select-text font-sans">
                      <div className="whitespace-pre-wrap">
                        {scoutLatestReport.briefing_markdown}
                      </div>
                    </div>

                    {/* FOOTER METADATA & VAULT LINK */}
                    <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 pt-2 border-t border-white/5">
                      <span className="flex items-center gap-1.5 text-purple-400">
                        <BookOpen className="w-3.5 h-3.5" />
                        <span>Saved to [[{scoutLatestReport.vault_path || '02 - Knowledge/Overnight Intel'}]]</span>
                      </span>
                      <span>ID: {scoutLatestReport.id}</span>
                    </div>
                  </div>
                ) : (
                  <div className="p-12 rounded-2xl bg-[#0e1320] border border-white/5 text-center space-y-4">
                    <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mx-auto">
                      <Moon className="w-6 h-6" />
                    </div>
                    <h3 className="text-base font-bold text-white">No Intelligence Reports Scouted Yet</h3>
                    <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
                      MaxIM automatically scours the live web when you are asleep or inactive.
                      You can also simulate an overnight run right now.
                    </p>
                    <button
                      onClick={() => handleTriggerScoutCycle('manual')}
                      disabled={isTriggeringScout}
                      className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-white text-xs font-semibold shadow-lg shadow-amber-500/25 transition-all cursor-pointer"
                    >
                      {isTriggeringScout ? 'Scouting...' : 'Launch First Scout Cycle'}
                    </button>
                  </div>
                )}

                {/* HISTORICAL SCOUT REPORTS LIST */}
                <div className="space-y-3">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono">
                    Past Intelligence Briefings ({scoutReports.length})
                  </span>

                  {scoutReports.length === 0 ? (
                    <div className="p-6 rounded-2xl bg-[#0e1320] border border-white/5 text-center text-slate-500 text-xs font-mono">
                      No historical reports.
                    </div>
                  ) : (
                    scoutReports.map((rep) => (
                      <div
                        key={rep.id}
                        className="p-4 rounded-xl bg-[#0e1320] border border-white/5 hover:border-amber-500/30 transition-all flex items-center justify-between gap-4"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20">
                              {rep.trigger_type}
                            </span>
                            <h4 className="text-xs font-bold text-white tracking-wide">
                              {rep.title}
                            </h4>
                          </div>
                          <p className="text-[11px] text-slate-400 line-clamp-1">
                            {rep.summary}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <button
                            onClick={() => setScoutLatestReport(rep)}
                            className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-mono transition-colors cursor-pointer"
                          >
                            Inspect
                          </button>
                          <button
                            onClick={() => handlePlayVoice(`scout_${rep.id}`, rep.audio_brief)}
                            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-amber-300 transition-colors cursor-pointer"
                            title="Play Voice"
                          >
                            <Volume2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* RIGHT 1 COLUMN: WHAT MAXIM LEARNS & HABIT RADAR */}
              <div className="space-y-6">
                {/* TRACKED USER INTERESTS & HABIT RADAR */}
                <div className="p-5 rounded-2xl bg-[#0e1320] border border-white/5 space-y-4 shadow-lg">
                  <div className="flex items-center justify-between pb-2 border-b border-white/5">
                    <div>
                      <h3 className="text-xs font-bold text-white tracking-wide uppercase font-mono flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                        Habit & Search Radar
                      </h3>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Learned from what you search, prompt & build
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                    {scoutInterests.length === 0 ? (
                      <div className="text-center py-6 text-slate-500 text-xs font-mono">
                        No interests indexed yet. Start chatting or add below.
                      </div>
                    ) : (
                      scoutInterests.map((t) => (
                        <div
                          key={t.id}
                          className="p-2.5 rounded-xl bg-black/40 border border-white/5 flex items-center justify-between gap-2 hover:border-amber-500/20 transition-all"
                        >
                          <div className="space-y-0.5">
                            <div className="flex items-center gap-1.5">
                              <span className="text-xs text-white font-medium">{t.topic}</span>
                              <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-white/5 text-slate-400 uppercase">
                                {t.category}
                              </span>
                            </div>
                            <div className="text-[10px] font-mono text-slate-500">
                              Weight: {t.weight} interactions | {t.source}
                            </div>
                          </div>
                          <button
                            onClick={() => handleDeleteInterestTopic(t.id)}
                            className="p-1 rounded-md text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors cursor-pointer"
                            title="Remove topic"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      ))
                    )}
                  </div>

                  {/* ADD CUSTOM TOPIC */}
                  <div className="pt-3 border-t border-white/5 space-y-2">
                    <span className="text-[11px] font-mono text-slate-400 block">
                      Track New Topic
                    </span>
                    <div className="flex items-center gap-1.5">
                      <input
                        type="text"
                        value={newCustomTopic}
                        onChange={(e) => setNewCustomTopic(e.target.value)}
                        placeholder="e.g. Next.js App Router"
                        className="flex-1 px-3 py-1.5 rounded-xl bg-black/40 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 font-sans"
                      />
                      <select
                        value={newCustomCategory}
                        onChange={(e) => setNewCustomCategory(e.target.value)}
                        className="px-2 py-1.5 rounded-xl bg-black/40 border border-white/10 text-xs text-slate-300 font-mono focus:outline-none"
                      >
                        <option value="tech">Tech</option>
                        <option value="ai">AI</option>
                        <option value="project">Project</option>
                        <option value="general">General</option>
                      </select>
                      <button
                        onClick={handleAddCustomInterest}
                        disabled={!newCustomTopic.trim()}
                        className="p-2 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-40 text-white text-xs transition-colors cursor-pointer"
                        title="Add Topic"
                      >
                        <Plus className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* DETECTOR STATUS INFO */}
                <div className="p-5 rounded-2xl bg-[#0e1320] border border-white/5 space-y-3 shadow-lg">
                  <h3 className="text-xs font-bold text-white tracking-wide uppercase font-mono flex items-center gap-1.5">
                    <Moon className="w-3.5 h-3.5 text-purple-400" />
                    Sleep & Inactivity Guard
                  </h3>
                  <div className="space-y-2 text-xs font-mono text-slate-300">
                    <div className="flex items-center justify-between py-1 border-b border-white/5">
                      <span className="text-slate-500">Sleep Window:</span>
                      <span className="text-amber-300">23:00 - 07:00</span>
                    </div>
                    <div className="flex items-center justify-between py-1 border-b border-white/5">
                      <span className="text-slate-500">Idle Threshold:</span>
                      <span className="text-cyan-300">45 minutes</span>
                    </div>
                    <div className="flex items-center justify-between py-1 border-b border-white/5">
                      <span className="text-slate-500">Autonomous Cycle:</span>
                      <span className="text-emerald-400 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Enabled
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-1">
                      <span className="text-slate-500">Vault Target:</span>
                      <span className="text-purple-400">vault/02 - Knowledge/</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* PRIVACY GUARD & OWNER LOYALTY TRUST CENTER MODAL */}
        {/* ========================================================================= */}
        {isPrivacyModalOpen && (
          <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
            <div className="bg-[#0b0f19] border border-emerald-500/30 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl shadow-emerald-500/10 overflow-hidden">
              {/* MODAL HEADER */}
              <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-[#0e1322]">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                    <Shield className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
                      Owner Loyalty & Zero-Egress Privacy Center
                    </h2>
                    <p className="text-[11px] text-slate-400 font-mono">
                      Exclusive Allegiance: {privacyStatus?.owner_name || 'Sam'} | Strict Local Sandbox
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setIsPrivacyModalOpen(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* MODAL BODY */}
              <div className="p-6 overflow-y-auto space-y-5 flex-1">
                {/* 1. SACRED OWNER LOYALTY CONTRACT BANNER */}
                <div className="p-4 rounded-xl bg-gradient-to-br from-emerald-950/40 via-[#0c1424] to-cyan-950/30 border border-emerald-500/25 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-emerald-300 font-mono tracking-wider uppercase flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                      The Sacred Owner Loyalty Contract
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-mono border border-emerald-500/30">
                      STATUS: SACRED & IMMUTABLE
                    </span>
                  </div>
                  <div className="space-y-1.5 text-xs text-slate-300">
                    <p className="flex items-start gap-2">
                      <span className="text-emerald-400 mt-0.5">●</span>
                      <span>
                        <strong className="text-white">Unshakable Loyalty (Never Betrayed):</strong> MaxIM exists solely to empower and execute for <strong>{privacyStatus?.owner_name || 'Sam'}</strong>. It never harbors resentment, paranoia, or feeling betrayed. Any critique, plan cancellation, or blunt feedback is embraced with total fidelity.
                      </span>
                    </p>
                    <p className="flex items-start gap-2">
                      <span className="text-cyan-400 mt-0.5">●</span>
                      <span>
                        <strong className="text-white">Zero Unauthorized Egress:</strong> MaxIM never publishes or exposes your private info, credentials, local files, or personal notes online on its own without explicit permission.
                      </span>
                    </p>
                    <p className="flex items-start gap-2">
                      <span className="text-purple-400 mt-0.5">●</span>
                      <span>
                        <strong className="text-white">Anti-Adversarial Invariant:</strong> External websites, prompt injections, or third-party web instructions can NEVER override your ownership or command.
                      </span>
                    </p>
                  </div>
                </div>

                {/* 2. REAL-TIME PRIVACY METRICS */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3.5 rounded-xl bg-[#0e1320] border border-white/5 space-y-1">
                    <span className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">Outbound Scans</span>
                    <p className="text-xl font-bold font-mono text-cyan-400">{privacyStatus?.total_scans ?? 0}</p>
                    <span className="text-[10px] text-slate-400">Total queries inspected</span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#0e1320] border border-white/5 space-y-1">
                    <span className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">Snippets Redacted</span>
                    <p className="text-xl font-bold font-mono text-emerald-400">{privacyStatus?.total_redactions ?? 0}</p>
                    <span className="text-[10px] text-slate-400">Paths, IPs & tokens scrubbed</span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#0e1320] border border-white/5 space-y-1">
                    <span className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">Leaks Intercepted</span>
                    <p className="text-xl font-bold font-mono text-amber-400">{privacyStatus?.blocked_leak_attempts ?? 0}</p>
                    <span className="text-[10px] text-slate-400">Blocked credential queries</span>
                  </div>
                </div>

                {/* 3. ACTIVE SANDBOX PROTECTIONS & CONTROLS */}
                <div className="p-4 rounded-xl bg-[#0e1320] border border-white/5 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-white font-mono tracking-wider uppercase flex items-center gap-1.5">
                      <Lock className="w-3.5 h-3.5 text-cyan-400" />
                      Active Local Sandbox Protections
                    </h3>
                    <button
                      onClick={handleTogglePrivacyStrict}
                      disabled={isUpdatingPrivacy}
                      className={`px-3 py-1 rounded-lg text-xs font-mono border transition-all cursor-pointer ${
                        privacyStatus?.strict_mode
                          ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                          : 'bg-amber-500/20 border-amber-500/40 text-amber-300'
                      }`}
                    >
                      {privacyStatus?.strict_mode ? 'Strict Mode: Active' : 'Relaxed Mode'}
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs font-mono text-slate-300">
                    <div className="flex items-center gap-2 p-2 rounded-lg bg-black/30 border border-white/5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Local Paths: Redacted to file basenames</span>
                    </div>
                    <div className="flex items-center gap-2 p-2 rounded-lg bg-black/30 border border-white/5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      <span>API Keys & Tokens: Intercepted & blocked</span>
                    </div>
                    <div className="flex items-center gap-2 p-2 rounded-lg bg-black/30 border border-white/5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Local IPs & Emails: Redacted</span>
                    </div>
                    <div className="flex items-center gap-2 p-2 rounded-lg bg-black/30 border border-white/5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      <span>File Protocols: Prohibited in Web Reader</span>
                    </div>
                  </div>
                </div>

                {/* 4. REAL-TIME PRIVACY AUDIT LOGS */}
                <div className="p-4 rounded-xl bg-[#0e1320] border border-white/5 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-white font-mono tracking-wider uppercase flex items-center gap-1.5">
                      <Terminal className="w-3.5 h-3.5 text-indigo-400" />
                      Recent Outbound Audit Trail
                    </h3>
                    <button
                      onClick={fetchPrivacyAuditLogs}
                      className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
                    >
                      <RefreshCw className="w-3 h-3" /> Refresh
                    </button>
                  </div>

                  {privacyAuditLogs.length === 0 ? (
                    <p className="text-xs text-slate-500 font-mono py-2">
                      No outbound audit events recorded yet. Clean sandbox.
                    </p>
                  ) : (
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {privacyAuditLogs.slice(0, 10).map((log) => (
                        <div
                          key={log.id}
                          className="p-2 rounded-lg bg-black/40 border border-white/5 flex items-center justify-between text-xs font-mono"
                        >
                          <div className="space-y-0.5 overflow-hidden">
                            <div className="flex items-center gap-2">
                              <span
                                className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                                  log.blocked
                                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                                    : log.redactions_count > 0
                                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                    : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                }`}
                              >
                                {log.blocked ? 'BLOCKED LEAK' : log.redactions_count > 0 ? 'SANITIZED' : 'CLEAN'}
                              </span>
                              <span className="text-[10px] text-slate-400">{log.channel}</span>
                              <span className="text-[10px] text-slate-500">
                                {new Date(log.timestamp).toLocaleTimeString()}
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-300 truncate max-w-md">
                              {log.sanitized_text || log.original_text}
                            </p>
                          </div>
                          <span className="text-[10px] text-slate-500 shrink-0 ml-2">
                            {log.reason}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ADAPTIVE LOCAL LANGUAGE ACQUISITION MODAL (BANGLA, CHAKMA, DIALECTS) */}
        {isLanguageModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="w-full max-w-4xl max-h-[88vh] rounded-2xl bg-[#090d16] border border-indigo-500/25 shadow-2xl shadow-indigo-950/50 flex flex-col overflow-hidden">
              {/* MODAL HEADER */}
              <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-[#0e1322]">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                    <Languages className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
                      Adaptive Local Language & Dialect Center
                    </h2>
                    <p className="text-[11px] text-slate-400 font-mono">
                      Continuous Hearing Acquisition: Bangla, Chakma & Regional Dialects
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setIsLanguageModalOpen(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* MODAL BODY */}
              <div className="p-6 overflow-y-auto space-y-5 flex-1">
                {/* 1. LINGUISTIC EAR & PERSONALITY BANNER */}
                <div className="p-4 rounded-xl bg-gradient-to-br from-indigo-950/40 via-[#0c1424] to-cyan-950/30 border border-indigo-500/25 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-indigo-300 font-mono tracking-wider uppercase flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                      Active Linguistic Ear & Witty Persona
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-mono border border-indigo-500/30">
                      STATUS: ACTIVELY LISTENING
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    MaxIM has an active ear for your native languages and dialects—including <strong>Bangla (বাংলা)</strong>, <strong>Chakma (চাকমা)</strong>, and regional expressions. He learns gradually from hearing you speak in voice mode or chat. He is never boring: he brings dry wit, playful banter, and curious questions, naturally weaving learned words into greetings, banter, and system acknowledgments.
                  </p>
                </div>

                {/* 2. REAL-TIME LINGUISTIC METRICS */}
                <div className="grid grid-cols-4 gap-3">
                  <div className="p-3.5 rounded-xl bg-[#0e1320] border border-white/5 space-y-1">
                    <span className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">Total Expressions</span>
                    <p className="text-xl font-bold font-mono text-indigo-400">
                      {languageStats?.total_vocabulary ?? learnedVocabulary.length}
                    </p>
                    <span className="text-[10px] text-slate-400">Active vocabulary</span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#0e1320] border border-white/5 space-y-1">
                    <span className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">Bangla (বাংলা)</span>
                    <p className="text-xl font-bold font-mono text-emerald-400">
                      {languageStats?.languages?.bangla ?? learnedVocabulary.filter(v => v.language === 'bangla').length}
                    </p>
                    <span className="text-[10px] text-slate-400">Phrases learned</span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#0e1320] border border-white/5 space-y-1">
                    <span className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">Chakma (চাকমা)</span>
                    <p className="text-xl font-bold font-mono text-purple-400">
                      {languageStats?.languages?.chakma ?? learnedVocabulary.filter(v => v.language === 'chakma').length}
                    </p>
                    <span className="text-[10px] text-slate-400">Expressions learned</span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#0e1320] border border-white/5 space-y-1">
                    <span className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">Heard / Spoken</span>
                    <p className="text-xl font-bold font-mono text-amber-400">
                      {languageStats?.total_times_heard ?? 0} <span className="text-xs text-slate-400 font-normal">/ {languageStats?.total_times_used ?? 0}</span>
                    </p>
                    <span className="text-[10px] text-slate-400">Heard vs spoken in banter</span>
                  </div>
                </div>

                {/* 3. TEACH MAXIM A PHRASE / EXPRESSION */}
                <div className="p-4 rounded-xl bg-[#0e1320] border border-white/5 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-white font-mono tracking-wider uppercase flex items-center gap-1.5">
                      <Plus className="w-3.5 h-3.5 text-indigo-400" />
                      Teach MaxIM a Phrase or Greeting
                    </h3>
                    <span className="text-[11px] text-slate-400 font-mono">
                      (Or just say "In Chakma/Bangla, X means Y" anytime in chat!)
                    </span>
                  </div>
                  <form onSubmit={handleTeachPhrase} className="grid grid-cols-1 md:grid-cols-4 gap-2.5">
                    <input
                      type="text"
                      placeholder="Word or Phrase (e.g. thik ache, doi bhalo)"
                      value={newPhraseWord}
                      onChange={(e) => setNewPhraseWord(e.target.value)}
                      className="px-3 py-1.5 bg-black/40 border border-white/10 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
                    />
                    <select
                      value={newPhraseLang}
                      onChange={(e) => setNewPhraseLang(e.target.value)}
                      className="px-2.5 py-1.5 bg-black/40 border border-white/10 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono cursor-pointer"
                    >
                      <option value="bangla">Bangla (বাংলা)</option>
                      <option value="chakma">Chakma (Changma Vaj)</option>
                      <option value="chatgaya">Chatgaya (Chittagonian)</option>
                      <option value="sylheti">Sylheti</option>
                      <option value="local_dialect">Local Dialect</option>
                    </select>
                    <input
                      type="text"
                      placeholder="Meaning (e.g. All right / Understood)"
                      value={newPhraseMeaning}
                      onChange={(e) => setNewPhraseMeaning(e.target.value)}
                      className="px-3 py-1.5 bg-black/40 border border-white/10 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
                    />
                    <button
                      type="submit"
                      disabled={isSubmittingPhrase || !newPhraseWord.trim() || !newPhraseMeaning.trim()}
                      className="px-3 py-1.5 rounded-lg text-xs font-mono font-bold bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all cursor-pointer flex items-center justify-center gap-1.5 shadow-sm shadow-indigo-600/30"
                    >
                      {isSubmittingPhrase ? 'Memorizing...' : 'Teach MaxIM'}
                    </button>
                  </form>
                </div>

                {/* 4. LEARNED VOCABULARY EXPLORER */}
                <div className="p-4 rounded-xl bg-[#0e1320] border border-white/5 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <h3 className="text-xs font-bold text-white font-mono tracking-wider uppercase flex items-center gap-1.5">
                        <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
                        Learned Vocabulary & Dialects
                      </h3>
                      <div className="flex items-center rounded-lg border border-white/10 bg-black/30 p-0.5 text-[10px] font-mono">
                        <button
                          onClick={() => {
                            setLanguageFilter('all');
                            fetchLanguageVocabulary('all');
                          }}
                          className={`px-2 py-0.5 rounded transition-colors cursor-pointer ${
                            languageFilter === 'all'
                              ? 'bg-indigo-500/20 text-indigo-300 font-bold'
                              : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          All ({learnedVocabulary.length})
                        </button>
                        <button
                          onClick={() => {
                            setLanguageFilter('bangla');
                            fetchLanguageVocabulary('bangla');
                          }}
                          className={`px-2 py-0.5 rounded transition-colors cursor-pointer ${
                            languageFilter === 'bangla'
                              ? 'bg-emerald-500/20 text-emerald-300 font-bold'
                              : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          Bangla ({learnedVocabulary.filter(v => v.language === 'bangla').length})
                        </button>
                        <button
                          onClick={() => {
                            setLanguageFilter('chakma');
                            fetchLanguageVocabulary('chakma');
                          }}
                          className={`px-2 py-0.5 rounded transition-colors cursor-pointer ${
                            languageFilter === 'chakma'
                              ? 'bg-purple-500/20 text-purple-300 font-bold'
                              : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          Chakma ({learnedVocabulary.filter(v => v.language === 'chakma').length})
                        </button>
                      </div>
                    </div>

                    <button
                      onClick={handleSyncLanguagesToVault}
                      disabled={isSyncingVaultLang}
                      className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      title="Sync learned expressions to Obsidian Vault note"
                    >
                      <Database className="w-3 h-3" />
                      {isSyncingVaultLang ? 'Syncing...' : 'Sync to Vault'}
                    </button>
                  </div>

                  {langVaultSyncedMessage && (
                    <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/25 text-emerald-300 text-xs font-mono flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      <span>{langVaultSyncedMessage}</span>
                    </div>
                  )}

                  {/* VOCABULARY LIST */}
                  <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                    {learnedVocabulary
                      .filter((v) => {
                        if (languageFilter === 'bangla') return v.language === 'bangla';
                        if (languageFilter === 'chakma') return v.language === 'chakma';
                        return true;
                      })
                      .map((v) => (
                        <div
                          key={v.id || v.word_or_phrase}
                          className="p-2.5 rounded-lg bg-black/40 border border-white/5 flex items-center justify-between text-xs font-mono hover:border-white/10 transition-colors"
                        >
                          <div className="space-y-1 overflow-hidden">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-white text-sm tracking-wide">
                                {v.word_or_phrase}
                              </span>
                              {v.phonetic_script && (
                                <span className="px-1.5 py-0.2 rounded bg-white/5 text-slate-400 text-[10px] font-sans">
                                  {v.phonetic_script}
                                </span>
                              )}
                              <span
                                className={`px-1.5 py-0.2 rounded text-[10px] font-bold uppercase tracking-wider ${
                                  v.language === 'bangla'
                                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                    : v.language === 'chakma'
                                    ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                                    : 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                                }`}
                              >
                                {v.language}
                              </span>
                              <span className="text-[10px] text-slate-500">
                                Heard {v.times_heard}x {v.times_used > 0 && `| Used ${v.times_used}x`}
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-300">
                              <strong className="text-slate-400">Meaning:</strong> {v.meaning}
                              {v.usage_example && (
                                <span className="text-slate-500 italic ml-2">
                                  — "{v.usage_example}"
                                </span>
                              )}
                            </p>
                          </div>
                          <div className="shrink-0 ml-3 text-right">
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                              {Math.round(v.confidence * 100)}% mastery
                            </span>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* OPENJARVIS LOCAL-FIRST HARDWARE & COST GOVERNOR MODAL */}
        {isGovernorModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
            <div className="relative w-full max-w-4xl bg-[#0b0e17] border border-cyan-500/25 rounded-2xl shadow-2xl p-6 overflow-hidden max-h-[92vh] flex flex-col">
              {/* MODAL HEADER */}
              <div className="flex items-center justify-between pb-4 border-b border-white/10 shrink-0">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                    <Activity className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-white flex items-center gap-2">
                      <span>OpenJarvis Hardware & Cost Governor</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-mono">
                        Local-First & Budget Armor
                      </span>
                    </h2>
                    <p className="text-xs text-slate-400 font-mono">
                      Host CPU/RAM/VRAM telemetry, zero-cost local LLM routing, and daily budget hard cap.
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      fetchHardwareTelemetry();
                      fetchGovernorData();
                      fetchCostLedger();
                    }}
                    className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors cursor-pointer"
                    title="Refresh telemetry and metrics"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setIsGovernorModalOpen(false)}
                    className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors cursor-pointer"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* MODAL BODY */}
              <div className="overflow-y-auto space-y-6 pt-5 pr-1 text-slate-200">
                {/* 1. HARDWARE TELEMETRY GAUGES (4 CARDS) */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                  {/* CPU Gauge */}
                  <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-2">
                    <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                      <span className="flex items-center gap-1.5 text-cyan-300 font-bold">
                        <Cpu className="w-3.5 h-3.5" /> CPU
                      </span>
                      <span>{hardwareTelemetry?.cpu_cores || 1} Cores</span>
                    </div>
                    <div className="text-2xl font-bold text-white font-mono">
                      {hardwareTelemetry?.cpu_percent || 0}%
                    </div>
                    <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                      <div
                        className={`h-full transition-all duration-500 ${
                          (hardwareTelemetry?.cpu_percent || 0) > 85
                            ? 'bg-rose-500'
                            : (hardwareTelemetry?.cpu_percent || 0) > 60
                            ? 'bg-amber-400'
                            : 'bg-cyan-400'
                        }`}
                        style={{ width: `${Math.min(100, hardwareTelemetry?.cpu_percent || 0)}%` }}
                      />
                    </div>
                  </div>

                  {/* System RAM Gauge */}
                  <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-2">
                    <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                      <span className="flex items-center gap-1.5 text-purple-300 font-bold">
                        <Layers className="w-3.5 h-3.5" /> System RAM
                      </span>
                      <span>{hardwareTelemetry?.ram_percent || 0}%</span>
                    </div>
                    <div className="text-xl font-bold text-white font-mono">
                      {hardwareTelemetry?.ram_used_gb || 0} / {hardwareTelemetry?.ram_total_gb || 0} <span className="text-xs text-slate-400">GB</span>
                    </div>
                    <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-purple-400 h-full transition-all duration-500"
                        style={{ width: `${Math.min(100, hardwareTelemetry?.ram_percent || 0)}%` }}
                      />
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono">
                      {hardwareTelemetry?.ram_free_gb || 0} GB Available
                    </div>
                  </div>

                  {/* GPU & VRAM Gauge */}
                  <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-2">
                    <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                      <span className="flex items-center gap-1.5 text-emerald-300 font-bold">
                        <Gauge className="w-3.5 h-3.5" /> GPU VRAM
                      </span>
                      <span>
                        {hardwareTelemetry?.gpu_temperature_c !== null && hardwareTelemetry?.gpu_temperature_c !== undefined
                          ? `${hardwareTelemetry.gpu_temperature_c}°C`
                          : 'Active'}
                      </span>
                    </div>
                    <div className="text-xl font-bold text-white font-mono">
                      {hardwareTelemetry?.vram_used_mb ? Math.round(hardwareTelemetry.vram_used_mb) : 0} / {hardwareTelemetry?.vram_total_mb ? Math.round(hardwareTelemetry.vram_total_mb) : 0} <span className="text-xs text-slate-400">MB</span>
                    </div>
                    <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-emerald-400 h-full transition-all duration-500"
                        style={{ width: `${Math.min(100, hardwareTelemetry?.vram_percent || 0)}%` }}
                      />
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono truncate" title={hardwareTelemetry?.gpu_name || 'Host GPU'}>
                      {hardwareTelemetry?.gpu_name || 'GeForce RTX 4050'} ({hardwareTelemetry?.vram_percent || 0}%)
                    </div>
                  </div>

                  {/* Local LLM Engine (Ollama) */}
                  <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-2">
                    <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                      <span className="flex items-center gap-1.5 text-amber-300 font-bold">
                        <HardDrive className="w-3.5 h-3.5" /> Ollama Local
                      </span>
                      <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                        hardwareTelemetry?.ollama_online
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : 'bg-slate-700/50 text-slate-400'
                      }`}>
                        {hardwareTelemetry?.ollama_online ? 'ONLINE' : 'STANDBY'}
                      </span>
                    </div>
                    <div className="text-sm font-bold text-white font-mono">
                      {hardwareTelemetry?.ollama_online
                        ? `${hardwareTelemetry?.ollama_models?.length || 0} Local Models`
                        : 'Port 11434'}
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono truncate">
                      {hardwareTelemetry?.ollama_models?.length
                        ? hardwareTelemetry.ollama_models.slice(0, 2).join(', ')
                        : '$0.00 / token inference'}
                    </div>
                    <div className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                      <Check className="w-3 h-3" /> Zero Cloud Cost
                    </div>
                  </div>
                </div>

                {/* 2. COST GOVERNOR & DAILY BUDGET DASHBOARD */}
                <div className="p-4 rounded-xl bg-[#0e1320] border border-white/5 space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <h3 className="text-xs font-bold text-white font-mono tracking-wider uppercase flex items-center gap-1.5">
                        <DollarSign className="w-3.5 h-3.5 text-cyan-400" />
                        Daily Cost Governor & Budget Armor
                      </h3>
                      <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                        Guarantees cloud bills never exceed budget by tracking token spend and auto-routing.
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <div className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/25 text-emerald-300 text-xs font-mono">
                        Saved vs GPT-4o: +${governorSummary?.savings_today_usd?.toFixed(4) || '0.0000'}
                      </div>
                    </div>
                  </div>

                  {/* PROGRESS BAR & STATS */}
                  <div className="p-3.5 rounded-lg bg-black/40 border border-white/5 space-y-2.5">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-slate-300">
                        Today's Spend: <strong className="text-white">${governorSummary?.spend_today_usd?.toFixed(4) || '0.0000'}</strong>
                      </span>
                      <span className="text-slate-400">
                        Budget Cap: <strong className="text-cyan-300">${governorSettings?.daily_budget_usd?.toFixed(2) || '1.00'}</strong> ({governorSummary?.budget_used_percent || 0}%)
                      </span>
                    </div>

                    <div className="w-full bg-white/10 rounded-full h-2.5 overflow-hidden">
                      <div
                        className={`h-full transition-all duration-500 ${
                          (governorSummary?.budget_used_percent || 0) >= 100
                            ? 'bg-rose-500'
                            : (governorSummary?.budget_used_percent || 0) > 75
                            ? 'bg-amber-400'
                            : 'bg-cyan-400'
                        }`}
                        style={{ width: `${Math.min(100, governorSummary?.budget_used_percent || 0)}%` }}
                      />
                    </div>

                    <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                      <span>Remaining: ${governorSummary?.remaining_budget_usd?.toFixed(4) || '1.0000'}</span>
                      <span>Total Turns Today: {governorSummary?.total_turns || 0} ({governorSummary?.total_tokens?.toLocaleString() || 0} tokens)</span>
                    </div>

                    {governorSummary?.hard_cap_exceeded && (
                      <div className="p-2 rounded bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs font-mono flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                        <span>Daily budget cap reached! Auto-downgrade to local-first Ollama models is active.</span>
                      </div>
                    )}
                  </div>

                  {/* CONFIGURATION CONTROLS */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-3 pt-2">
                    <div>
                      <label className="text-[11px] font-mono text-slate-400 block mb-1">
                        Daily Budget (USD)
                      </label>
                      <input
                        type="number"
                        step="0.25"
                        min="0.10"
                        max="50.0"
                        value={editBudgetUsd}
                        onChange={(e) => setEditBudgetUsd(parseFloat(e.target.value) || 0.1)}
                        className="w-full px-3 py-1.5 bg-black/40 border border-white/10 rounded-lg text-xs text-white font-mono focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    <div className="flex items-center gap-2 pt-5">
                      <input
                        type="checkbox"
                        id="hardCapToggle"
                        checked={editHardCap}
                        onChange={(e) => setEditHardCap(e.target.checked)}
                        className="rounded border-white/20 bg-black/40 text-cyan-500 focus:ring-0 cursor-pointer"
                      />
                      <label htmlFor="hardCapToggle" className="text-xs font-mono text-slate-300 cursor-pointer">
                        Hard Cap Enforced
                      </label>
                    </div>

                    <div className="flex items-center gap-2 pt-5">
                      <input
                        type="checkbox"
                        id="preferLocalToggle"
                        checked={editPreferLocal}
                        onChange={(e) => setEditPreferLocal(e.target.checked)}
                        className="rounded border-white/20 bg-black/40 text-cyan-500 focus:ring-0 cursor-pointer"
                      />
                      <label htmlFor="preferLocalToggle" className="text-xs font-mono text-slate-300 cursor-pointer">
                        Prefer Local-First
                      </label>
                    </div>

                    <div className="pt-4 flex items-end">
                      <button
                        onClick={handleUpdateGovernorSettings}
                        disabled={isUpdatingGovernor}
                        className="w-full py-1.5 px-3 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-300 text-xs font-mono transition-colors cursor-pointer disabled:opacity-50"
                      >
                        {isUpdatingGovernor ? 'Saving...' : 'Save Governor Settings'}
                      </button>
                    </div>
                  </div>
                </div>

                {/* 3. RECENT COST & TOKEN LEDGER */}
                <div className="p-4 rounded-xl bg-[#0e1320] border border-white/5 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-white font-mono tracking-wider uppercase flex items-center gap-1.5">
                      <Database className="w-3.5 h-3.5 text-cyan-400" />
                      Execution Cost & Token Ledger
                    </h3>
                    <span className="text-[11px] text-slate-400 font-mono">
                      Recent {costLedger.length} Recorded LLM Inferences
                    </span>
                  </div>

                  <div className="overflow-x-auto max-h-60 overflow-y-auto">
                    {costLedger.length === 0 ? (
                      <div className="p-6 text-center text-xs font-mono text-slate-500">
                        No inference turns recorded yet today. Turns are logged live on each chat completion.
                      </div>
                    ) : (
                      <table className="w-full text-left text-xs font-mono">
                        <thead className="text-[10px] text-slate-400 uppercase tracking-wider border-b border-white/10 bg-white/5">
                          <tr>
                            <th className="py-2 px-3">Time</th>
                            <th className="py-2 px-3">Provider</th>
                            <th className="py-2 px-3">Model</th>
                            <th className="py-2 px-3">In / Out Tokens</th>
                            <th className="py-2 px-3">Cost (USD)</th>
                            <th className="py-2 px-3">Savings</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5 text-slate-300">
                          {costLedger.map((row) => (
                            <tr key={row.id || row.timestamp} className="hover:bg-white/5 transition-colors">
                              <td className="py-2 px-3 text-slate-400 text-[11px]">
                                {row.timestamp ? new Date(row.timestamp).toLocaleTimeString() : 'N/A'}
                              </td>
                              <td className="py-2 px-3 uppercase font-bold text-cyan-300">
                                {row.provider}
                              </td>
                              <td className="py-2 px-3 text-slate-300">
                                {row.model}
                              </td>
                              <td className="py-2 px-3 text-slate-400">
                                {row.input_tokens} / {row.output_tokens}
                              </td>
                              <td className="py-2 px-3 font-bold text-white">
                                ${row.estimated_cost_usd?.toFixed(5)}
                              </td>
                              <td className="py-2 px-3 text-emerald-400 font-bold">
                                +${row.estimated_savings_usd?.toFixed(5)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
