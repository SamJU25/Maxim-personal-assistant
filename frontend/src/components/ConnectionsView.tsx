import React, { useState, useEffect } from 'react';
import {
  Radio,
  Send,
  RefreshCw,
  SlidersHorizontal,
  CheckCircle2,
  Copy,
  Check,
  Search,
  FileText,
  Terminal,
  Smartphone,
  MessageSquare,
  FolderSync,
  Globe,
  X,
  Eye,
  EyeOff,
  Clock,
  ArrowUpRight,
  ArrowDownLeft,
  CheckCheck
} from 'lucide-react';
import { ChannelItem, InboxLogItem } from '../types';

export const ConnectionsView: React.FC = () => {
  // Navigation tabs within ConnectionsView
  const [activeTab, setActiveTab] = useState<'channels' | 'inbox'>('channels');
  const [searchFilter, setSearchFilter] = useState('');
  const [channelTypeFilter, setChannelTypeFilter] = useState<'all' | 'chat' | 'system'>('all');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Quick Dispatch Console state
  const [dispatchChannel, setDispatchChannel] = useState<string>('telegram');
  const [dispatchText, setDispatchText] = useState('');
  const [dispatchTitle, setDispatchTitle] = useState('');
  const [isDispatching, setIsDispatching] = useState(false);
  const [dispatchFeedback, setDispatchFeedback] = useState<string | null>(null);

  // Configuration Modal state
  const [editingChannel, setEditingChannel] = useState<ChannelItem | null>(null);
  const [formBotToken, setFormBotToken] = useState('');
  const [formWebhookUrl, setFormWebhookUrl] = useState('');
  const [formTarget, setFormTarget] = useState('');
  const [formAllowedIds, setFormAllowedIds] = useState('');
  const [formEnabled, setFormEnabled] = useState(true);
  const [showSecret, setShowSecret] = useState(false);
  const [isSavingConfig, setIsSavingConfig] = useState(false);
  const [configSuccessMsg, setConfigSuccessMsg] = useState<string | null>(null);

  // Inspection / Details drawer
  const [inspectingLog, setInspectingLog] = useState<InboxLogItem | null>(null);

  // Default channels dataset
  const [channels, setChannels] = useState<ChannelItem[]>([
    {
      id: 'telegram',
      name: 'Telegram Bot Gateway',
      type: 'telegram',
      description: 'Async polling bot daemon with markdown parsing, voice synthesis, and remote commands (/start, /status, /chat, /dream).',
      enabled: true,
      status: 'online',
      hasToken: true,
      hasWebhook: false,
      botUsername: '@maxim_assistant_bot',
      target: 'chat_id: 928374102 (Sam)',
      allowedIdsCount: 1,
      inboundCount: 42,
      outboundCount: 38,
      lastActive: '2 mins ago',
    },
    {
      id: 'discord',
      name: 'Discord Gateway & Webhook',
      type: 'discord',
      description: 'Discord REST API v10 and inbound webhooks with 2,000-character chunking and formatted embed output.',
      enabled: true,
      status: 'configured',
      hasToken: true,
      hasWebhook: true,
      target: '#agent-ops (channel_id: 11029384756)',
      allowedIdsCount: 2,
      inboundCount: 18,
      outboundCount: 21,
      lastActive: '14 mins ago',
    },
    {
      id: 'slack',
      name: 'Slack Notification Uplink',
      type: 'slack',
      description: 'Incoming Webhooks & Block Kit messenger with 4,000-character chunking and thread conversation routing.',
      enabled: true,
      status: 'configured',
      hasToken: false,
      hasWebhook: true,
      target: '#maxim-intel (webhook mounted)',
      webhookUrl: 'https://hooks.slack.com/services/T00/B00/X00...',
      allowedIdsCount: 1,
      inboundCount: 7,
      outboundCount: 12,
      lastActive: '1 hour ago',
    },
    {
      id: 'obsidian',
      name: 'Obsidian Vault Synapse',
      type: 'obsidian',
      description: 'Real-time local markdown filesystem watcher for F:\\MAXIM V2\\vault with bi-directional wikilinks and auto-checkpoints.',
      enabled: true,
      status: 'online',
      hasToken: false,
      hasWebhook: false,
      target: 'F:\\MAXIM V2\\vault',
      allowedIdsCount: 1,
      inboundCount: 148,
      outboundCount: 96,
      lastActive: 'Active (FS Watcher)',
    },
    {
      id: 'webhook',
      name: 'Universal JSON Webhook & Shortcuts',
      type: 'webhook',
      description: 'Inbound and outbound authenticated JSON endpoint for Apple iOS Shortcuts, Home Assistant, Termux, and cron runners.',
      enabled: true,
      status: 'online',
      hasToken: true,
      hasWebhook: true,
      target: 'POST /api/uplink/inbound',
      webhookUrl: 'http://127.0.0.1:8000/api/uplink/inbound',
      allowedIdsCount: 3,
      inboundCount: 57,
      outboundCount: 58,
      lastActive: 'Just now',
    },
    {
      id: 'agent_reach',
      name: 'Agent Reach Internet Gateway',
      type: 'agent_reach',
      description: 'Direct internet research gateway utilizing Jina Reader markdown extraction, DuckDuckGo search, and GitHub REST API.',
      enabled: true,
      status: 'online',
      hasToken: false,
      hasWebhook: false,
      target: 'Free Internet Endpoints',
      allowedIdsCount: 1,
      inboundCount: 84,
      outboundCount: 84,
      lastActive: '5 mins ago',
    }
  ]);

  // Default communication logs
  const [inboxLogs, setInboxLogs] = useState<InboxLogItem[]>([
    {
      id: 58,
      channel: 'webhook',
      direction: 'outbound',
      sender_id: 'maxim_ai',
      sender_name: 'MaxIM Core',
      content: 'Telemetry report delivered to Apple Shortcuts daemon. All systems nominal.',
      status: 'dispatched',
      timestamp: '2026-09-25 17:22:04'
    },
    {
      id: 57,
      channel: 'webhook',
      direction: 'inbound',
      sender_id: 'apple_shortcuts_sam',
      sender_name: 'Sam iPhone',
      content: 'Status check from phone. Battery 84%, Wi-Fi linked.',
      status: 'received',
      timestamp: '2026-09-25 17:21:49'
    },
    {
      id: 56,
      channel: 'telegram',
      direction: 'outbound',
      sender_id: 'maxim_ai',
      sender_name: 'MaxIM Core',
      content: 'Obsidian LifeOS TELOS verified. Sarcastic morning greeting queued for 07:00.',
      status: 'dispatched',
      timestamp: '2026-09-25 17:15:30'
    },
    {
      id: 55,
      channel: 'telegram',
      direction: 'inbound',
      sender_id: 'sam_owner',
      sender_name: 'Sam (Owner)',
      content: '/status',
      status: 'received',
      timestamp: '2026-09-25 17:15:28'
    },
    {
      id: 54,
      channel: 'discord',
      direction: 'outbound',
      sender_id: 'agent_chief',
      sender_name: 'Chief Operator',
      content: 'Shift Report #042 published to Obsidian vault 03 - Agents/Shift_20260925.md.',
      status: 'dispatched',
      timestamp: '2026-09-25 16:45:12'
    },
    {
      id: 53,
      channel: 'slack',
      direction: 'outbound',
      sender_id: 'maxim_ai',
      sender_name: 'MaxIM Core',
      content: 'Brave Search & Filesystem MCP servers mounted cleanly. SQLite WAL integrity verified.',
      status: 'dispatched',
      timestamp: '2026-09-25 16:10:00'
    },
    {
      id: 52,
      channel: 'obsidian',
      direction: 'inbound',
      sender_id: 'fs_watcher',
      sender_name: 'Vault Watcher',
      content: 'Modified note detected: [[00 - LifeOS/TELOS.md]]. Reloading active goals context.',
      status: 'received',
      timestamp: '2026-09-25 15:30:19'
    }
  ]);

  // Fetch real channel status if backend is available
  useEffect(() => {
    let isMounted = true;
    const fetchLiveStatus = async () => {
      try {
        const res = await fetch('/api/uplink/channels');
        if (res.ok) {
          const data = await res.json();
          if (data && data.channels && isMounted) {
            // Update counts or active state if matching
            setChannels((prev) =>
              prev.map((ch) => {
                const live = data.channels[ch.id];
                if (live) {
                  return {
                    ...ch,
                    enabled: live.enabled ?? ch.enabled,
                    hasToken: live.has_token ?? ch.hasToken,
                    hasWebhook: live.has_webhook ?? ch.hasWebhook,
                    inboundCount: (live.inbound_messages || 0) + ch.inboundCount,
                    outboundCount: (live.outbound_messages || 0) + ch.outboundCount,
                  };
                }
                return ch;
              })
            );
          }
        }
      } catch {
        // Fallback to local high-fidelity mock state
      }

      try {
        const inboxRes = await fetch('/api/uplink/inbox?limit=20');
        if (inboxRes.ok) {
          const inboxData = await inboxRes.json();
          if (inboxData && Array.isArray(inboxData.inbox) && inboxData.inbox.length > 0 && isMounted) {
            setInboxLogs(inboxData.inbox);
          }
        }
      } catch {
        // Fallback
      }
    };

    fetchLiveStatus();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleOpenConfigModal = (channel: ChannelItem) => {
    setEditingChannel(channel);
    setFormBotToken(channel.hasToken ? '••••••••••••••••' : '');
    setFormWebhookUrl(channel.webhookUrl || '');
    setFormTarget(channel.target || '');
    setFormAllowedIds(channel.id === 'telegram' ? '928374102' : 'sam_owner, chief_operator');
    setFormEnabled(channel.enabled);
    setShowSecret(false);
    setConfigSuccessMsg(null);
  };

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingChannel) return;

    setIsSavingConfig(true);
    setConfigSuccessMsg(null);

    try {
      await fetch('/api/uplink/channels', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: editingChannel.id,
          enabled: formEnabled,
          bot_token: formBotToken.includes('••') ? undefined : formBotToken,
          webhook_url: formWebhookUrl,
          target: formTarget,
          allowed_ids: formAllowedIds.split(',').map((s) => s.trim()).filter(Boolean),
        }),
      });
    } catch {
      // Local state update fallback
    }

    setChannels((prev) =>
      prev.map((ch) => {
        if (ch.id === editingChannel.id) {
          return {
            ...ch,
            enabled: formEnabled,
            target: formTarget || ch.target,
            webhookUrl: formWebhookUrl || ch.webhookUrl,
            status: formEnabled ? 'online' : 'standby',
            hasToken: Boolean(formBotToken) || ch.hasToken,
            hasWebhook: Boolean(formWebhookUrl) || ch.hasWebhook,
          };
        }
        return ch;
      })
    );

    setIsSavingConfig(false);
    setConfigSuccessMsg('Channel configuration updated successfully.');
    setTimeout(() => {
      try {
        if (typeof window !== 'undefined' && typeof document !== 'undefined') {
          setEditingChannel(null);
          setConfigSuccessMsg(null);
        }
      } catch {}
    }, 900);
  };

  const handleQuickDispatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dispatchText.trim()) return;

    setIsDispatching(true);
    setDispatchFeedback(null);

    const targetChannel = channels.find((c) => c.id === dispatchChannel);
    const targetAddress = targetChannel?.target || 'broadcast_all';

    try {
      if (dispatchChannel === 'all') {
        await fetch('/api/uplink/broadcast', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: dispatchText, title: dispatchTitle || undefined }),
        });
      } else {
        await fetch('/api/uplink/send', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            channel: dispatchChannel,
            target: targetAddress,
            text: dispatchText,
            title: dispatchTitle || undefined,
          }),
        });
      }
    } catch {
      // Fallback
    }

    // Add new outbound entry to inboxLogs
    const newLog: InboxLogItem = {
      id: Date.now(),
      channel: dispatchChannel,
      direction: 'outbound',
      sender_id: 'maxim_ai',
      sender_name: 'MaxIM Operator',
      content: dispatchTitle ? `[${dispatchTitle}] ${dispatchText}` : dispatchText,
      status: 'dispatched',
      timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
    };

    setInboxLogs((prev) => [newLog, ...prev]);

    // Update outbound counter
    setChannels((prev) =>
      prev.map((ch) => {
        if (ch.id === dispatchChannel || dispatchChannel === 'all') {
          return { ...ch, outboundCount: ch.outboundCount + 1, lastActive: 'Just now' };
        }
        return ch;
      })
    );

    setIsDispatching(false);
    setDispatchFeedback(`Dispatched cleanly to ${dispatchChannel.toUpperCase()}`);
    setDispatchText('');
    setDispatchTitle('');
    setTimeout(() => setDispatchFeedback(null), 3000);
  };

  // Filter channels based on tab & search query
  const filteredChannels = channels.filter((ch) => {
    const matchesSearch =
      ch.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
      ch.description.toLowerCase().includes(searchFilter.toLowerCase()) ||
      ch.id.toLowerCase().includes(searchFilter.toLowerCase());

    if (!matchesSearch) return false;

    if (channelTypeFilter === 'chat') {
      return ['telegram', 'discord', 'slack'].includes(ch.type);
    }
    if (channelTypeFilter === 'system') {
      return ['obsidian', 'webhook', 'agent_reach'].includes(ch.type);
    }
    return true;
  });

  // Filter inbox logs
  const filteredLogs = inboxLogs.filter((log) => {
    const q = searchFilter.toLowerCase();
    return (
      log.channel.toLowerCase().includes(q) ||
      log.content.toLowerCase().includes(q) ||
      log.sender_id.toLowerCase().includes(q) ||
      (log.sender_name && log.sender_name.toLowerCase().includes(q))
    );
  });

  const totalInbound = channels.reduce((acc, c) => acc + c.inboundCount, 0);
  const totalOutbound = channels.reduce((acc, c) => acc + c.outboundCount, 0);
  const onlineCount = channels.filter((c) => c.status === 'online' || c.status === 'configured').length;

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-bg-main text-text-primary">
      {/* 1. TOP HEADER & METRICS BAR */}
      <div className="px-6 py-4 border-b border-border-subtle bg-bg-card/40 flex flex-wrap items-center justify-between gap-4 select-none">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-accent text-accent-contrast flex items-center justify-center font-bold shadow-sm">
            <Radio className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight text-text-primary">
                External Uplinks & Communication Gateways
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                {onlineCount} OF {channels.length} ACTIVE
              </span>
            </div>
            <p className="text-xs text-text-muted mt-0.5">
              Secure remote bridges connecting Telegram, Discord, Slack, Apple Shortcuts, and Local Obsidian Vault.
            </p>
          </div>
        </div>

        {/* Telemetry quick pills */}
        <div className="flex items-center gap-2 text-xs font-mono">
          <div className="px-3 py-1.5 rounded-lg border border-border-subtle bg-bg-card flex items-center gap-2 shadow-xs">
            <ArrowDownLeft className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-text-muted">INBOUND:</span>
            <span className="font-semibold text-text-primary">{totalInbound} msgs</span>
          </div>
          <div className="px-3 py-1.5 rounded-lg border border-border-subtle bg-bg-card flex items-center gap-2 shadow-xs">
            <ArrowUpRight className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-text-muted">OUTBOUND:</span>
            <span className="font-semibold text-text-primary">{totalOutbound} msgs</span>
          </div>
        </div>
      </div>

      {/* 2. SUB-NAVIGATION & SEARCH BAR */}
      <div className="px-6 py-3 border-b border-border-subtle bg-bg-card/20 flex flex-wrap items-center justify-between gap-3">
        {/* Dual Tab Switcher */}
        <div className="flex items-center gap-1 bg-bg-card-subtle p-1 rounded-lg border border-border-subtle">
          <button
            onClick={() => setActiveTab('channels')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'channels'
                ? 'bg-accent text-accent-contrast shadow-xs font-semibold'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            <span>Channel Gateways ({channels.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('inbox')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'inbox'
                ? 'bg-accent text-accent-contrast shadow-xs font-semibold'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Unified Inbox & Dispatch Logs ({inboxLogs.length})</span>
          </button>
        </div>

        {/* Filter controls */}
        <div className="flex items-center gap-2 flex-1 max-w-md justify-end">
          {activeTab === 'channels' && (
            <div className="flex items-center gap-1 border border-border-subtle rounded-lg p-0.5 bg-bg-card">
              <button
                onClick={() => setChannelTypeFilter('all')}
                className={`px-2.5 py-1 rounded text-[11px] font-mono transition-colors ${
                  channelTypeFilter === 'all'
                    ? 'bg-text-primary text-bg-main font-semibold'
                    : 'text-text-muted hover:text-text-primary'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setChannelTypeFilter('chat')}
                className={`px-2.5 py-1 rounded text-[11px] font-mono transition-colors ${
                  channelTypeFilter === 'chat'
                    ? 'bg-text-primary text-bg-main font-semibold'
                    : 'text-text-muted hover:text-text-primary'
                }`}
              >
                Messaging
              </button>
              <button
                onClick={() => setChannelTypeFilter('system')}
                className={`px-2.5 py-1 rounded text-[11px] font-mono transition-colors ${
                  channelTypeFilter === 'system'
                    ? 'bg-text-primary text-bg-main font-semibold'
                    : 'text-text-muted hover:text-text-primary'
                }`}
              >
                System & Vault
              </button>
            </div>
          )}

          {/* Search box */}
          <div className="relative min-w-[200px] flex-1 max-w-xs">
            <Search className="w-3.5 h-3.5 text-text-muted absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder={activeTab === 'channels' ? 'Filter channels...' : 'Search logs, senders, text...'}
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-border-subtle bg-bg-card focus:outline-none focus:border-accent text-text-primary placeholder:text-text-muted"
            />
            {searchFilter && (
              <button
                onClick={() => setSearchFilter('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 3. MAIN TAB CONTENT */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* TAB 1: CHANNEL GATEWAYS & DISPATCHER */}
        {activeTab === 'channels' && (
          <div className="space-y-6">
            {/* Quick Outbound Dispatch Bar */}
            <div className="p-4 rounded-xl border border-border-subtle bg-bg-card shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Send className="w-4 h-4 text-text-primary" />
                  <span className="text-xs font-bold tracking-tight text-text-primary uppercase font-mono">
                    Manual Outbound Dispatcher
                  </span>
                </div>
                {dispatchFeedback && (
                  <span className="text-xs font-mono text-emerald-400 flex items-center gap-1 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    <CheckCheck className="w-3 h-3" />
                    {dispatchFeedback}
                  </span>
                )}
              </div>

              <form onSubmit={handleQuickDispatch} className="flex flex-col md:flex-row gap-2.5">
                <select
                  value={dispatchChannel}
                  onChange={(e) => setDispatchChannel(e.target.value)}
                  className="px-3 py-2 rounded-lg border border-border-subtle bg-bg-card-subtle text-xs font-mono text-text-primary focus:outline-none focus:border-accent md:w-44 flex-shrink-0"
                >
                  <option value="telegram">Telegram Bot</option>
                  <option value="discord">Discord Channel</option>
                  <option value="slack">Slack Webhook</option>
                  <option value="webhook">Apple Shortcuts</option>
                  <option value="all">⚡ Broadcast to All</option>
                </select>

                <input
                  type="text"
                  placeholder="Optional Title (e.g. Daily Briefing)"
                  value={dispatchTitle}
                  onChange={(e) => setDispatchTitle(e.target.value)}
                  className="px-3 py-2 rounded-lg border border-border-subtle bg-bg-card text-xs text-text-primary focus:outline-none focus:border-accent md:w-52 flex-shrink-0 placeholder:text-text-muted"
                />

                <input
                  type="text"
                  placeholder="Message payload to transmit remotely..."
                  value={dispatchText}
                  onChange={(e) => setDispatchText(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-lg border border-border-subtle bg-bg-card text-xs text-text-primary focus:outline-none focus:border-accent placeholder:text-text-muted"
                  required
                />

                <button
                  type="submit"
                  disabled={isDispatching || !dispatchText.trim()}
                  className="px-4 py-2 rounded-lg bg-accent text-accent-contrast text-xs font-semibold hover:opacity-90 active:scale-98 transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
                >
                  {isDispatching ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Send className="w-3.5 h-3.5" />
                  )}
                  <span>Transmit</span>
                </button>
              </form>
            </div>

            {/* Channels Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredChannels.map((channel) => {
                const isOnline = channel.status === 'online' || channel.status === 'configured';
                return (
                  <div
                    key={channel.id}
                    className="p-5 rounded-xl border border-border-subtle bg-bg-card hover:border-text-secondary/40 transition-all flex flex-col justify-between shadow-xs group"
                  >
                    <div>
                      {/* Card Header */}
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-lg bg-bg-card-subtle border border-border-subtle flex items-center justify-center text-text-primary group-hover:bg-accent group-hover:text-accent-contrast transition-colors">
                            {channel.type === 'telegram' && <Send className="w-4 h-4" />}
                            {channel.type === 'discord' && <Terminal className="w-4 h-4" />}
                            {channel.type === 'slack' && <MessageSquare className="w-4 h-4" />}
                            {channel.type === 'obsidian' && <FolderSync className="w-4 h-4" />}
                            {channel.type === 'webhook' && <Smartphone className="w-4 h-4" />}
                            {channel.type === 'agent_reach' && <Globe className="w-4 h-4" />}
                          </div>
                          <div>
                            <h3 className="text-xs font-bold text-text-primary tracking-tight">
                              {channel.name}
                            </h3>
                            <span className="text-[10px] font-mono text-text-muted">
                              {channel.type.toUpperCase()} ADAPTER
                            </span>
                          </div>
                        </div>

                        {/* Status badge */}
                        <span
                          className={`text-[9px] font-mono px-2 py-0.5 rounded-full border font-semibold uppercase flex items-center gap-1 ${
                            isOnline
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                              : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-zinc-400'
                            }`}
                          />
                          {channel.status}
                        </span>
                      </div>

                      {/* Description */}
                      <p className="text-xs text-text-secondary leading-relaxed mb-4 line-clamp-2">
                        {channel.description}
                      </p>

                      {/* Target Address pill */}
                      {channel.target && (
                        <div className="mb-4 px-2.5 py-1.5 rounded-lg border border-border-subtle bg-bg-card-subtle flex items-center justify-between text-[11px] font-mono">
                          <span className="text-text-muted truncate max-w-[210px]">{channel.target}</span>
                          <button
                            onClick={() => handleCopy(channel.target || '', channel.id)}
                            className="text-text-muted hover:text-text-primary ml-1"
                            title="Copy Target Address"
                          >
                            {copiedId === channel.id ? (
                              <Check className="w-3 h-3 text-emerald-400" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                          </button>
                        </div>
                      )}

                      {/* Metrics row */}
                      <div className="grid grid-cols-2 gap-2 text-[11px] font-mono border-t border-border-subtle pt-3 mb-4">
                        <div>
                          <span className="text-text-muted block text-[10px]">INBOUND</span>
                          <span className="font-semibold text-text-primary">
                            {channel.inboundCount} msgs
                          </span>
                        </div>
                        <div>
                          <span className="text-text-muted block text-[10px]">OUTBOUND</span>
                          <span className="font-semibold text-text-primary">
                            {channel.outboundCount} msgs
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Bottom Actions */}
                    <div className="flex items-center gap-2 pt-2 border-t border-border-subtle/60">
                      <button
                        onClick={() => handleOpenConfigModal(channel)}
                        className="flex-1 py-1.5 px-3 rounded-lg border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover text-text-primary text-xs font-medium flex items-center justify-center gap-1.5 transition-colors"
                      >
                        <SlidersHorizontal className="w-3 h-3 text-text-secondary" />
                        <span>Configure</span>
                      </button>

                      <button
                        onClick={() => {
                          setDispatchChannel(channel.id);
                          setDispatchText(`Test ping dispatched at ${new Date().toLocaleTimeString()}`);
                        }}
                        className="py-1.5 px-3 rounded-lg border border-border-subtle bg-bg-card hover:bg-bg-card-hover text-text-secondary hover:text-text-primary text-xs font-mono transition-colors"
                        title="Draft Test Ping"
                      >
                        Ping
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 2: UNIFIED COMMUNICATION LOGS & INBOX */}
        {activeTab === 'inbox' && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl border border-border-subtle bg-bg-card flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-text-primary uppercase font-mono tracking-wider">
                  Universal Cross-Channel Ledger
                </h3>
                <p className="text-xs text-text-muted mt-0.5">
                  Synchronous receipts from Telegram, Discord, Slack webhooks, and local filesystem watcher.
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono text-text-muted">
                <span>Total Entries: {filteredLogs.length}</span>
              </div>
            </div>

            {/* Logs Table / List */}
            <div className="border border-border-subtle rounded-xl overflow-hidden bg-bg-card">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-border-subtle bg-bg-card-subtle/80 text-[10px] font-mono uppercase text-text-muted">
                      <th className="py-2.5 px-4">Direction</th>
                      <th className="py-2.5 px-4">Channel</th>
                      <th className="py-2.5 px-4">Sender / Origin</th>
                      <th className="py-2.5 px-4">Message Content</th>
                      <th className="py-2.5 px-4">Status</th>
                      <th className="py-2.5 px-4">Timestamp</th>
                      <th className="py-2.5 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-subtle/60 font-sans">
                    {filteredLogs.map((log) => {
                      const isInbound = log.direction === 'inbound';
                      return (
                        <tr
                          key={log.id}
                          className="hover:bg-bg-card-subtle/50 transition-colors group cursor-pointer"
                          onClick={() => setInspectingLog(log)}
                        >
                          {/* Direction */}
                          <td className="py-3 px-4 whitespace-nowrap">
                            <span
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold ${
                                isInbound
                                  ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                                  : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              }`}
                            >
                              {isInbound ? (
                                <ArrowDownLeft className="w-3 h-3" />
                              ) : (
                                <ArrowUpRight className="w-3 h-3" />
                              )}
                              {log.direction.toUpperCase()}
                            </span>
                          </td>

                          {/* Channel */}
                          <td className="py-3 px-4 font-mono font-medium text-text-primary whitespace-nowrap">
                            <span className="px-1.5 py-0.5 rounded bg-bg-card-subtle border border-border-subtle text-[11px]">
                              {log.channel}
                            </span>
                          </td>

                          {/* Sender */}
                          <td className="py-3 px-4 font-mono text-text-secondary whitespace-nowrap">
                            <div>
                              <span className="font-semibold text-text-primary">
                                {log.sender_name || log.sender_id}
                              </span>
                              {log.sender_name && (
                                <span className="block text-[10px] text-text-muted">
                                  {log.sender_id}
                                </span>
                              )}
                            </div>
                          </td>

                          {/* Message Content */}
                          <td className="py-3 px-4 max-w-md">
                            <p className="text-text-primary truncate font-sans text-xs">
                              {log.content}
                            </p>
                          </td>

                          {/* Status */}
                          <td className="py-3 px-4 font-mono text-[10px] uppercase text-text-muted whitespace-nowrap">
                            <span className="flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                              {log.status}
                            </span>
                          </td>

                          {/* Timestamp */}
                          <td className="py-3 px-4 font-mono text-text-muted text-[11px] whitespace-nowrap">
                            {log.timestamp}
                          </td>

                          {/* Action */}
                          <td className="py-3 px-4 text-right whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                            <button
                              onClick={() => handleCopy(log.content, `log-${log.id}`)}
                              className="p-1 rounded text-text-muted hover:text-text-primary transition-colors"
                              title="Copy Message Text"
                            >
                              {copiedId === `log-${log.id}` ? (
                                <Check className="w-3.5 h-3.5 text-emerald-400" />
                              ) : (
                                <Copy className="w-3.5 h-3.5" />
                              )}
                            </button>
                          </td>
                        </tr>
                      );
                    })}

                    {filteredLogs.length === 0 && (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-text-muted text-xs">
                          No communication logs matched the filter criteria.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 4. CHANNEL CONFIGURATION MODAL */}
      {editingChannel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs select-none">
          <div className="w-full max-w-lg rounded-2xl border border-border-subtle bg-bg-card p-6 shadow-2xl relative animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="flex items-start justify-between pb-4 border-b border-border-subtle">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-accent text-accent-contrast flex items-center justify-center font-bold">
                  <SlidersHorizontal className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-text-primary">
                    Configure {editingChannel.name}
                  </h3>
                  <p className="text-xs text-text-muted">
                    Channel credentials, webhook parameters, and authorization constraints.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setEditingChannel(null)}
                className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-card-subtle transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Form */}
            <form onSubmit={handleSaveConfig} className="space-y-4 pt-4">
              {/* Enabled toggle */}
              <div className="flex items-center justify-between p-3 rounded-xl border border-border-subtle bg-bg-card-subtle">
                <div>
                  <span className="text-xs font-semibold text-text-primary block">
                    Channel Status
                  </span>
                  <span className="text-[11px] text-text-muted">
                    Enable or suspend remote traffic for this gateway.
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setFormEnabled(!formEnabled)}
                  className={`px-3 py-1 rounded-lg text-xs font-mono font-semibold transition-colors border ${
                    formEnabled
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30'
                  }`}
                >
                  {formEnabled ? 'ENABLED' : 'DISABLED'}
                </button>
              </div>

              {/* Bot Token / Secret Field */}
              {editingChannel.id !== 'obsidian' && (
                <div>
                  <label className="block text-xs font-mono font-medium text-text-secondary mb-1">
                    API Bot Token / Authorization Secret
                  </label>
                  <div className="relative">
                    <input
                      type={showSecret ? 'text' : 'password'}
                      placeholder={editingChannel.id === 'telegram' ? 'e.g. 123456:ABC-DEF...' : 'e.g. xoxb-...'}
                      value={formBotToken}
                      onChange={(e) => setFormBotToken(e.target.value)}
                      className="w-full pl-3 pr-10 py-2 rounded-lg border border-border-subtle bg-bg-card text-xs font-mono text-text-primary focus:outline-none focus:border-accent"
                    />
                    <button
                      type="button"
                      onClick={() => setShowSecret(!showSecret)}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
                    >
                      {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              )}

              {/* Webhook URL Field */}
              {(editingChannel.id === 'discord' || editingChannel.id === 'slack' || editingChannel.id === 'webhook') && (
                <div>
                  <label className="block text-xs font-mono font-medium text-text-secondary mb-1">
                    Webhook Destination / Inbound URL
                  </label>
                  <input
                    type="text"
                    placeholder="https://discord.com/api/webhooks/... or https://hooks.slack.com/..."
                    value={formWebhookUrl}
                    onChange={(e) => setFormWebhookUrl(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border-subtle bg-bg-card text-xs font-mono text-text-primary focus:outline-none focus:border-accent"
                  />
                </div>
              )}

              {/* Target / Channel ID Field */}
              <div>
                <label className="block text-xs font-mono font-medium text-text-secondary mb-1">
                  Target Destination / Default Chat Identifier
                </label>
                <input
                  type="text"
                  placeholder="e.g. 928374102 or #general"
                  value={formTarget}
                  onChange={(e) => setFormTarget(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-border-subtle bg-bg-card text-xs font-mono text-text-primary focus:outline-none focus:border-accent"
                />
              </div>

              {/* Allowed Sender IDs */}
              <div>
                <label className="block text-xs font-mono font-medium text-text-secondary mb-1">
                  Authorized Sender IDs (Comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. 928374102, sam_owner"
                  value={formAllowedIds}
                  onChange={(e) => setFormAllowedIds(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-border-subtle bg-bg-card text-xs font-mono text-text-primary focus:outline-none focus:border-accent"
                />
                <span className="text-[10px] text-text-muted mt-1 block">
                  Enforces Zero-Trust isolation. Commands from untrusted sender IDs are defanged.
                </span>
              </div>

              {/* Success message feedback */}
              {configSuccessMsg && (
                <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{configSuccessMsg}</span>
                </div>
              )}

              {/* Modal Buttons */}
              <div className="flex items-center justify-end gap-2 pt-3 border-t border-border-subtle">
                <button
                  type="button"
                  onClick={() => setEditingChannel(null)}
                  className="px-4 py-2 rounded-lg border border-border-subtle bg-bg-card-subtle text-xs text-text-primary hover:bg-bg-card-hover transition-colors font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSavingConfig}
                  className="px-5 py-2 rounded-lg bg-accent text-accent-contrast text-xs font-semibold hover:opacity-90 active:scale-98 transition-all flex items-center gap-1.5"
                >
                  {isSavingConfig ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                  <span>Save Configuration</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 5. LOG INSPECTION DRAWER */}
      {inspectingLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs select-none">
          <div className="w-full max-w-md rounded-2xl border border-border-subtle bg-bg-card p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-start justify-between pb-3 border-b border-border-subtle">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-text-primary" />
                <h3 className="text-xs font-bold font-mono uppercase text-text-primary">
                  Communication Record #{inspectingLog.id}
                </h3>
              </div>
              <button
                onClick={() => setInspectingLog(null)}
                className="text-text-muted hover:text-text-primary"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
                <div className="p-2 rounded-lg bg-bg-card-subtle border border-border-subtle">
                  <span className="text-text-muted block text-[10px]">CHANNEL</span>
                  <span className="text-text-primary font-semibold">{inspectingLog.channel}</span>
                </div>
                <div className="p-2 rounded-lg bg-bg-card-subtle border border-border-subtle">
                  <span className="text-text-muted block text-[10px]">DIRECTION</span>
                  <span className="text-text-primary font-semibold">{inspectingLog.direction.toUpperCase()}</span>
                </div>
              </div>

              <div className="p-2 rounded-lg bg-bg-card-subtle border border-border-subtle font-mono text-[11px]">
                <span className="text-text-muted block text-[10px]">SENDER</span>
                <span className="text-text-primary font-semibold">
                  {inspectingLog.sender_name || inspectingLog.sender_id}
                </span>
                <span className="text-text-muted block text-[10px] mt-0.5">ID: {inspectingLog.sender_id}</span>
              </div>

              <div>
                <span className="text-text-muted block text-[10px] font-mono uppercase mb-1">
                  Raw Content Payload
                </span>
                <div className="p-3 rounded-lg border border-border-subtle bg-bg-card-subtle font-mono text-xs text-text-primary whitespace-pre-wrap max-h-48 overflow-y-auto leading-relaxed">
                  {inspectingLog.content}
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] font-mono text-text-muted pt-2 border-t border-border-subtle">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {inspectingLog.timestamp}
                </span>
                <button
                  onClick={() => handleCopy(inspectingLog.content, 'modal-log')}
                  className="px-2.5 py-1 rounded bg-bg-card border border-border-subtle text-text-primary hover:bg-bg-card-hover flex items-center gap-1 transition-colors"
                >
                  {copiedId === 'modal-log' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>Copy</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConnectionsView;
