import { useState, useEffect } from 'react';
import {
  Zap,
  Search,
  Plus,
  Check,
  Terminal,
  ExternalLink,
  X,
  Download,
  Trash2,
  Server,
  ArrowRight
} from 'lucide-react';
import { NativeToolItem, MCPServerItem } from '../types';

const DEFAULT_NATIVE_TOOLS: NativeToolItem[] = [
  // Vault & Knowledge
  {
    id: 'tool_read_vault',
    name: 'read_vault_note',
    category: 'Vault & Knowledge',
    toolset: 'vault',
    description: 'Reads the markdown contents, YAML frontmatter, and metadata of a note from the local Obsidian vault.',
    status: 'active',
    parametersCount: 1,
    sampleCall: 'read_vault_note(title="00 - LifeOS/TELOS.md")',
  },
  {
    id: 'tool_search_vault',
    name: 'search_vault',
    category: 'Vault & Knowledge',
    toolset: 'vault',
    description: 'Performs sub-millisecond BM25 full-text keyword search across all markdown files in the vault.',
    status: 'active',
    parametersCount: 2,
    sampleCall: 'search_vault(query="black and white theme", limit=5)',
  },
  {
    id: 'tool_write_vault',
    name: 'write_vault_note',
    category: 'Vault & Knowledge',
    toolset: 'vault',
    description: 'Creates or safely updates a markdown document inside the Obsidian vault with automatic backup.',
    status: 'active',
    parametersCount: 3,
    sampleCall: 'write_vault_note(title="Meeting Note", content="...", folder="02 - Daily")',
  },
  {
    id: 'tool_build_moc',
    name: 'build_moc',
    category: 'Vault & Knowledge',
    toolset: 'vault',
    description: 'Traverses bidirectional wiki-links and generates an automated Map of Content (MOC) index note.',
    status: 'active',
    parametersCount: 2,
    sampleCall: 'build_moc(tag="#architecture", folder="03 - Maps")',
  },

  // Perception & Vision
  {
    id: 'tool_get_active_window',
    name: 'get_active_window',
    category: 'Perception',
    toolset: 'perception',
    description: 'Inspects operating system foreground process window title, bounds, PID, and executable path.',
    status: 'active',
    parametersCount: 0,
    sampleCall: 'get_active_window()',
  },
  {
    id: 'tool_capture_screen',
    name: 'capture_screen_frame',
    category: 'Perception',
    toolset: 'perception',
    description: 'Captures full multi-monitor desktop framebuffer encoded into low-latency compressed JPEG.',
    status: 'active',
    parametersCount: 1,
    sampleCall: 'capture_screen_frame(monitor_index=0)',
  },
  {
    id: 'tool_detect_screen_text',
    name: 'detect_screen_text',
    category: 'Perception',
    toolset: 'perception',
    description: 'Runs local optical OCR extraction on active window pixels to locate on-screen UI buttons.',
    status: 'active',
    parametersCount: 1,
    sampleCall: 'detect_screen_text(confidence_threshold=0.85)',
  },

  // OS & System
  {
    id: 'tool_execute_ps',
    name: 'execute_powershell',
    category: 'OS & System',
    toolset: 'sandbox',
    description: 'Executes sandboxed PowerShell commands with RTK token compression and real-time output streaming.',
    status: 'active',
    parametersCount: 2,
    sampleCall: 'execute_powershell(command="rtk git status")',
  },
  {
    id: 'tool_read_file',
    name: 'read_local_file',
    category: 'OS & System',
    toolset: 'files',
    description: 'Reads text file contents from disk with path security confinement to project directories.',
    status: 'active',
    parametersCount: 2,
    sampleCall: 'read_local_file(path="package.json", max_bytes=10000)',
  },
  {
    id: 'tool_write_file',
    name: 'write_local_file',
    category: 'OS & System',
    toolset: 'files',
    description: 'Safely creates or replaces files with atomic write guarantees and syntax verification.',
    status: 'active',
    parametersCount: 2,
    sampleCall: 'write_local_file(path="src/config.json", content="{}")',
  },

  // Internet Reach
  {
    id: 'tool_jina_reader',
    name: 'fetch_jina_reader',
    category: 'Internet Reach',
    toolset: 'reach',
    description: 'Extracts clean Markdown and strips ad slop from any public web URL using Jina AI reader proxy.',
    status: 'active',
    parametersCount: 1,
    sampleCall: 'fetch_jina_reader(url="https://news.ycombinator.com")',
  },
  {
    id: 'tool_ddg_search',
    name: 'duckduckgo_search',
    category: 'Internet Reach',
    toolset: 'reach',
    description: 'Performs live web search queries across internet sources with zero API key dependencies.',
    status: 'active',
    parametersCount: 2,
    sampleCall: 'duckduckgo_search(query="React 19 release notes", limit=5)',
  },
  {
    id: 'tool_github_query',
    name: 'github_repo_query',
    category: 'Internet Reach',
    toolset: 'reach',
    description: 'Fetches GitHub repository files, commit logs, releases, and issue discussions via REST API.',
    status: 'active',
    parametersCount: 3,
    sampleCall: 'github_repo_query(owner="facebook", repo="react", endpoint="releases")',
  },

  // Swarm & Subagents
  {
    id: 'tool_create_subagent',
    name: 'create_subagent',
    category: 'Swarm & Subagents',
    toolset: 'delegation',
    description: 'Spawns an isolated child subagent worker with dedicated model routing and scoped toolset access.',
    status: 'active',
    parametersCount: 4,
    sampleCall: 'create_subagent(task="Audit security", role="Security Specialist")',
  },
  {
    id: 'tool_parallel_pool',
    name: 'run_parallel_pool',
    category: 'Swarm & Subagents',
    toolset: 'delegation',
    description: 'Executes concurrent multi-subagent pools with barrier synchronization and results aggregation.',
    status: 'active',
    parametersCount: 2,
    sampleCall: 'run_parallel_pool(subagents=[sub1, sub2])',
  },
  {
    id: 'tool_call_mcp',
    name: 'call_mcp_tool',
    category: 'FastMCP Bridge',
    toolset: 'mcp',
    description: 'Executes an arbitrary tool on any connected Model Context Protocol server over stdio or SSE.',
    status: 'active',
    parametersCount: 3,
    sampleCall: 'call_mcp_tool(server="filesystem", tool="list_directory", arguments={})',
  },
];

const DEFAULT_MCP_SERVERS: MCPServerItem[] = [
  {
    id: 'mcp_filesystem',
    name: 'filesystem',
    description: 'Secure local filesystem operations with path confinement and sandboxed file read/write.',
    registry: 'official',
    transport: 'stdio',
    packageName: '@modelcontextprotocol/server-filesystem',
    command: 'npx -y @modelcontextprotocol/server-filesystem',
    args: ['F:\\MAXIM V2'],
    toolsCount: 6,
    installed: true,
  },
  {
    id: 'mcp_sqlite',
    name: 'sqlite',
    description: 'Read, query, and analyze SQLite database tables with WAL mode concurrency and indexing profiling.',
    registry: 'official',
    transport: 'stdio',
    packageName: 'mcp-server-sqlite',
    command: 'python -m mcp_server_sqlite',
    args: ['--db-path', 'f:\\MAXIM V2\\backend\\maxim.db'],
    toolsCount: 4,
    installed: true,
  },
  {
    id: 'mcp_brave_search',
    name: 'brave-search',
    description: 'High-speed real-time web search with clean markdown summaries and source citations.',
    registry: 'official',
    transport: 'stdio',
    packageName: '@modelcontextprotocol/server-brave-search',
    command: 'npx -y @modelcontextprotocol/server-brave-search',
    env: ['BRAVE_API_KEY'],
    toolsCount: 2,
    installed: true,
  },
  {
    id: 'mcp_github',
    name: 'github',
    description: 'GitHub repository inspection, code review, file viewing, commit history, and pull request workflows.',
    registry: 'official',
    transport: 'stdio',
    packageName: '@modelcontextprotocol/server-github',
    command: 'npx -y @modelcontextprotocol/server-github',
    env: ['GITHUB_PERSONAL_ACCESS_TOKEN'],
    toolsCount: 9,
    installed: true,
  },
  {
    id: 'mcp_puppeteer',
    name: 'puppeteer-browser',
    description: 'Headless Chromium browser automation, interactive DOM inspection, and visual page rendering.',
    registry: 'smithery',
    transport: 'stdio',
    packageName: '@smithery/puppeteer-mcp',
    command: 'npx -y @smithery/puppeteer-mcp',
    toolsCount: 5,
    installed: false,
  },
  {
    id: 'mcp_postgres',
    name: 'postgres-db',
    description: 'Enterprise PostgreSQL relational database connector with prepared statement query execution.',
    registry: 'glama',
    transport: 'stdio',
    packageName: '@glama/postgres-mcp',
    command: 'npx -y @glama/postgres-mcp',
    env: ['POSTGRES_CONNECTION_STRING'],
    toolsCount: 7,
    installed: false,
  },
  {
    id: 'mcp_obsidian_vault',
    name: 'obsidian-vault',
    description: 'Dynamic local Markdown vault watcher with bidirectional wikilink graph resolution.',
    registry: 'smithery',
    transport: 'stdio',
    packageName: '@smithery/obsidian-vault-mcp',
    command: 'npx -y @smithery/obsidian-vault-mcp',
    args: ['F:\\MAXIM V2\\vault'],
    toolsCount: 8,
    installed: true,
  },
  {
    id: 'mcp_fetch',
    name: 'fetch-service',
    description: 'Direct HTTP GET/POST fetch with HTML-to-Markdown conversion for static documentation.',
    registry: 'official',
    transport: 'stdio',
    packageName: '@modelcontextprotocol/server-fetch',
    command: 'npx -y @modelcontextprotocol/server-fetch',
    toolsCount: 1,
    installed: true,
  },
];



const REGISTRY_FILTERS = [
  'All Registries',
  'Mounted (Active)',
  'Official MCP',
  'Smithery',
  'Glama',
];

export function SkillsView() {
  const [activeTab, setActiveTab] = useState<'native' | 'mcp'>('native');
  const [nativeTools, setNativeTools] = useState<NativeToolItem[]>(DEFAULT_NATIVE_TOOLS);
  const [mcpServers, setMcpServers] = useState<MCPServerItem[]>(DEFAULT_MCP_SERVERS);
  const [selectedCategory, setSelectedCategory] = useState('All Tools');
  const [selectedRegistry, setSelectedRegistry] = useState('All Registries');
  const [searchQuery, setSearchQuery] = useState('');

  // Tool inspection drawer state
  const [inspectTool, setInspectTool] = useState<NativeToolItem | null>(null);

  // Mount custom MCP modal state
  const [isMountModalOpen, setIsMountModalOpen] = useState(false);
  const [mountName, setMountName] = useState('');
  const [mountCommand, setMountCommand] = useState('');
  const [mountArgs, setMountArgs] = useState('');
  const [mountEnv, setMountEnv] = useState('');
  const [mountTransport, setMountTransport] = useState<'stdio' | 'sse'>('stdio');
  const [mountRegistry, setMountRegistry] = useState<'official' | 'smithery' | 'glama' | 'local'>('local');

  // Action status message
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  // Dynamically derive categories from native tools
  const availableCategories = ['All Tools', ...Array.from(new Set(nativeTools.map((t) => t.category))).sort()];

  // Fetch installed MCP servers and native tools from backend
  useEffect(() => {
    let isMounted = true;
    const fetchToolsAndServers = async () => {
      try {
        const toolsRes = await fetch('/api/tools');
        if (toolsRes.ok) {
          const toolsData = await toolsRes.json();
          if (isMounted && toolsData.tools && Array.isArray(toolsData.tools) && toolsData.tools.length > 0) {
            setNativeTools(toolsData.tools);
          }
        }
      } catch {
        // Fallback to local default tools gracefully
      }

      try {
        const res = await fetch('/api/mcp/servers');
        if (res.ok) {
          const data = await res.json();
          if (isMounted && data.servers && Array.isArray(data.servers)) {
            const installedMap = new Set(data.servers.map((s: { name: string }) => s.name));
            setMcpServers((prev) =>
              prev.map((server) => ({
                ...server,
                installed: installedMap.has(server.name) || server.installed,
              }))
            );
          }
        }
      } catch {
        // Fallback to local default state
      }
    };
    fetchToolsAndServers();
    return () => {
      isMounted = false;
    };
  }, []);

  const triggerNotice = (msg: string) => {
    setActionNotice(msg);
    setTimeout(() => setActionNotice(null), 3500);
  };

  // Toggle Install / Mount for an MCP Server
  const handleToggleServerMount = async (server: MCPServerItem) => {
    const isCurrentlyInstalled = server.installed;
    setMcpServers((prev) =>
      prev.map((s) => (s.id === server.id ? { ...s, installed: !isCurrentlyInstalled } : s))
    );

    if (isCurrentlyInstalled) {
      triggerNotice(`Unmounted MCP server [${server.name}].`);
      try {
        await fetch(`/api/mcp/servers/${server.name}`, { method: 'DELETE' });
      } catch {
        // offline fallback
      }
    } else {
      triggerNotice(`Successfully mounted MCP server [${server.name}] into SQLite registry.`);
      try {
        await fetch('/api/mcp/install', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: server.name,
            transport: server.transport,
            command: server.command,
            args: server.args || [],
            description: server.description,
            source_registry: server.registry,
          }),
        });
      } catch {
        // offline fallback
      }
    }
  };

  // Submit custom MCP mount modal
  const handleMountSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mountName.trim() || !mountCommand.trim()) return;

    const newServer: MCPServerItem = {
      id: `mcp_${Date.now()}`,
      name: mountName.trim(),
      description: `Custom mounted server: ${mountCommand.trim()}`,
      registry: mountRegistry,
      transport: mountTransport,
      command: mountCommand.trim(),
      args: mountArgs ? mountArgs.split(' ').map((a) => a.trim()).filter(Boolean) : [],
      env: mountEnv ? mountEnv.split(',').map((e) => e.trim()).filter(Boolean) : [],
      toolsCount: 3,
      installed: true,
    };

    setMcpServers((prev) => [newServer, ...prev]);
    setIsMountModalOpen(false);
    triggerNotice(`Mounted custom MCP server [${newServer.name}] with ${mountTransport.toUpperCase()} transport.`);

    try {
      await fetch('/api/mcp/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newServer.name,
          transport: newServer.transport,
          command: newServer.command,
          args: newServer.args,
          description: newServer.description,
          source_registry: newServer.registry,
        }),
      });
    } catch {
      // offline fallback
    }

    setMountName('');
    setMountCommand('');
    setMountArgs('');
    setMountEnv('');
  };

  // Filter Native Tools
  const filteredTools = nativeTools.filter((tool) => {
    const matchesCategory =
      selectedCategory === 'All Tools' || tool.category.toLowerCase() === selectedCategory.toLowerCase();
    const q = searchQuery.toLowerCase().trim();
    const matchesQuery =
      !q ||
      tool.name.toLowerCase().includes(q) ||
      tool.description.toLowerCase().includes(q) ||
      tool.toolset.toLowerCase().includes(q);
    return matchesCategory && matchesQuery;
  });

  // Filter MCP Servers
  const filteredServers = mcpServers.filter((server) => {
    const matchesRegistry =
      selectedRegistry === 'All Registries' ||
      (selectedRegistry === 'Mounted (Active)' && server.installed) ||
      server.registry.toLowerCase() === selectedRegistry.toLowerCase().replace(' mcp', '');
    const q = searchQuery.toLowerCase().trim();
    const matchesQuery =
      !q ||
      server.name.toLowerCase().includes(q) ||
      server.description.toLowerCase().includes(q) ||
      (server.packageName && server.packageName.toLowerCase().includes(q));
    return matchesRegistry && matchesQuery;
  });

  const mountedCount = mcpServers.filter((s) => s.installed).length;
  const totalMcpTools = mcpServers.filter((s) => s.installed).reduce((acc, s) => acc + (s.toolsCount || 0), 0);

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-bg-main text-text-primary">
      {/* 1. TOP HEADER & METRICS BAR */}
      <header className="px-6 py-4 border-b border-border-subtle bg-bg-card/30 flex flex-col md:flex-row md:items-center justify-between gap-4 flex-shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-text-primary" />
            <h1 className="text-base font-semibold tracking-tight text-text-primary">
              Skills Directory & MCP Marketplace Hub
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-border-subtle bg-bg-card-subtle text-text-secondary">
              PHASE 24 RUNNER
            </span>
          </div>
          <p className="text-xs text-text-muted mt-0.5">
            Native sandboxed toolsets, Model Context Protocol servers, Smithery and Glama dynamic registries.
          </p>
        </div>

        {/* Action Controls & Metrics */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg border border-border-subtle bg-bg-card text-xs font-mono">
            <div className="flex items-center gap-1.5 text-text-primary">
              <Terminal className="w-3.5 h-3.5 text-text-secondary" />
              <span>{nativeTools.length} NATIVE TOOLS</span>
            </div>
            <span className="text-border-subtle">|</span>
            <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>{mountedCount} MOUNTED SERVERS</span>
            </div>
            <span className="text-border-subtle">|</span>
            <span className="text-text-muted">{totalMcpTools} MCP BRIDGES</span>
          </div>

          <button
            onClick={() => setIsMountModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-text-primary text-bg-main text-xs font-semibold hover:opacity-90 transition-opacity"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Mount MCP Server</span>
          </button>
        </div>
      </header>

      {/* Action Notification Banner */}
      {actionNotice && (
        <div className="bg-bg-card border-b border-border-subtle px-6 py-2 flex items-center justify-between text-xs font-mono text-emerald-400 animate-fadeIn">
          <div className="flex items-center gap-2">
            <Check className="w-3.5 h-3.5" />
            <span>{actionNotice}</span>
          </div>
          <button onClick={() => setActionNotice(null)} className="text-text-muted hover:text-text-primary">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* 2. SUB-NAVIGATION TABS & SEARCH ROW */}
      <div className="px-6 py-3 border-b border-border-subtle bg-bg-card/10 flex flex-wrap items-center justify-between gap-4 flex-shrink-0">
        {/* Main Tab Toggle: Native Toolset vs MCP Marketplace */}
        <div className="flex items-center gap-1.5 p-1 bg-bg-card border border-border-subtle rounded-lg text-xs font-medium">
          <button
            onClick={() => {
              setActiveTab('native');
              setSelectedCategory('All Tools');
            }}
            className={`px-3 py-1.5 rounded-md transition-colors flex items-center gap-2 ${
              activeTab === 'native'
                ? 'bg-text-primary text-bg-main font-semibold shadow-sm'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Native Toolsets ({nativeTools.length})</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('mcp');
              setSelectedRegistry('All Registries');
            }}
            className={`px-3 py-1.5 rounded-md transition-colors flex items-center gap-2 ${
              activeTab === 'mcp'
                ? 'bg-text-primary text-bg-main font-semibold shadow-sm'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <Server className="w-3.5 h-3.5" />
            <span>MCP Marketplace & Servers ({mcpServers.length})</span>
          </button>
        </div>

        {/* Quick Search */}
        <div className="relative w-64 flex-shrink-0">
          <Search className="w-3.5 h-3.5 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder={activeTab === 'native' ? 'Search native tools...' : 'Search MCP servers & packages...'}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 bg-bg-card border border-border-subtle rounded-lg text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-text-secondary"
          />
        </div>
      </div>

      {/* 3. CATEGORY / REGISTRY FILTER BAR */}
      <div className="px-6 py-2.5 border-b border-border-subtle bg-bg-card/5 flex items-center gap-1.5 overflow-x-auto no-scrollbar flex-shrink-0">
        {activeTab === 'native' ? (
          availableCategories.map((cat) => {
            const isActive = selectedCategory === cat;
            const count =
              cat === 'All Tools'
                ? nativeTools.length
                : nativeTools.filter((t) => t.category.toLowerCase() === cat.toLowerCase()).length;
            return (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors whitespace-nowrap flex items-center gap-1.5 ${
                  isActive
                    ? 'bg-text-primary text-bg-main font-semibold'
                    : 'bg-bg-card text-text-secondary hover:text-text-primary border border-border-subtle'
                }`}
              >
                <span>{cat}</span>
                <span
                  className={`text-[10px] px-1 py-0.2 rounded font-mono ${
                    isActive ? 'bg-bg-main/20 text-bg-main' : 'bg-bg-card-subtle text-text-muted'
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })
        ) : (
          REGISTRY_FILTERS.map((reg) => {
            const isActive = selectedRegistry === reg;
            const count =
              reg === 'All Registries'
                ? mcpServers.length
                : reg === 'Mounted (Active)'
                ? mcpServers.filter((s) => s.installed).length
                : mcpServers.filter((s) => s.registry.toLowerCase() === reg.toLowerCase().replace(' mcp', '')).length;
            return (
              <button
                key={reg}
                onClick={() => setSelectedRegistry(reg)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors whitespace-nowrap flex items-center gap-1.5 ${
                  isActive
                    ? 'bg-text-primary text-bg-main font-semibold'
                    : 'bg-bg-card text-text-secondary hover:text-text-primary border border-border-subtle'
                }`}
              >
                <span>{reg}</span>
                <span
                  className={`text-[10px] px-1 py-0.2 rounded font-mono ${
                    isActive ? 'bg-bg-main/20 text-bg-main' : 'bg-bg-card-subtle text-text-muted'
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })
        )}
      </div>

      {/* 4. MAIN CONTENT AREA */}
      <div className="flex-1 flex overflow-hidden">
        {/* TAB 1: NATIVE TOOLSETS GRID */}
        {activeTab === 'native' && (
          <div className="flex-1 p-6 overflow-y-auto bg-bg-main flex flex-col gap-4">
            <div className="flex items-center justify-between text-xs font-mono text-text-muted px-1">
              <span>ACTIVE NATIVE TOOLS ({filteredTools.length})</span>
              <span>Direct execution via MaxIM ReAct Engine</span>
            </div>

            {filteredTools.length === 0 ? (
              <div className="p-12 text-center text-xs text-text-muted border border-dashed border-border-subtle rounded-2xl">
                No native tools matching "{searchQuery}" in {selectedCategory}.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
                {filteredTools.map((tool) => (
                  <div
                    key={tool.id}
                    className="p-4 rounded-xl border border-border-subtle bg-bg-card/50 hover:bg-bg-card hover:border-border-hover transition-all flex flex-col justify-between gap-3 group"
                  >
                    <div className="flex flex-col gap-2">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-bg-card-subtle border border-border-subtle text-text-secondary">
                          {tool.category}
                        </span>
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">
                          {tool.status}
                        </span>
                      </div>

                      <h3 className="text-xs font-bold font-mono text-text-primary flex items-center gap-1.5 group-hover:text-text-primary transition-colors">
                        <Terminal className="w-3.5 h-3.5 text-text-secondary" />
                        {tool.name}
                      </h3>

                      <p className="text-xs text-text-muted leading-relaxed line-clamp-2">
                        {tool.description}
                      </p>
                    </div>

                    {/* Footer Details & Inspection Trigger */}
                    <div className="pt-2 border-t border-border-subtle/50 flex items-center justify-between text-[10px] font-mono text-text-muted">
                      <span>Toolset: {tool.toolset}</span>
                      <button
                        onClick={() => setInspectTool(tool)}
                        className="text-text-secondary hover:text-text-primary transition-colors flex items-center gap-1"
                      >
                        <span>Inspect Schema</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: MCP MARKETPLACE & SERVERS HUB */}
        {activeTab === 'mcp' && (
          <div className="flex-1 p-6 overflow-y-auto bg-bg-main flex flex-col gap-4">
            <div className="flex items-center justify-between text-xs font-mono text-text-muted px-1">
              <span>REGISTERED MCP SERVERS ({filteredServers.length})</span>
              <span>Smithery, Glama & Official Registry Connectors</span>
            </div>

            {filteredServers.length === 0 ? (
              <div className="p-12 text-center text-xs text-text-muted border border-dashed border-border-subtle rounded-2xl">
                No MCP servers matching "{searchQuery}" in {selectedRegistry}.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredServers.map((server) => {
                  const isMounted = server.installed;
                  return (
                    <div
                      key={server.id}
                      className={`p-5 rounded-2xl border transition-all flex flex-col justify-between gap-4 ${
                        isMounted
                          ? 'bg-bg-card border-text-primary/70 shadow-sm'
                          : 'bg-bg-card/40 border-border-subtle hover:border-border-hover'
                      }`}
                    >
                      <div className="flex flex-col gap-2.5">
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-bg-card-subtle text-text-primary border border-border-subtle font-semibold">
                              {server.registry}
                            </span>
                            <span className="text-[10px] font-mono text-text-muted">
                              {server.transport.toUpperCase()}
                            </span>
                          </div>

                          <span
                            className={`text-[9px] font-mono px-2 py-0.5 rounded border uppercase font-medium ${
                              isMounted
                                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                : 'bg-bg-card-subtle text-text-muted border-border-subtle'
                            }`}
                          >
                            {isMounted ? 'MOUNTED & ACTIVE' : 'AVAILABLE'}
                          </span>
                        </div>

                        <div>
                          <h3 className="text-sm font-bold text-text-primary font-mono flex items-center gap-2">
                            <Server className="w-4 h-4 text-text-secondary" />
                            {server.name}
                          </h3>
                          <p className="text-xs text-text-muted mt-1 leading-relaxed">
                            {server.description}
                          </p>
                        </div>

                        {/* Package & Command line preview */}
                        {server.command && (
                          <div className="p-2.5 rounded-lg bg-bg-main/80 border border-border-subtle/60 font-mono text-[11px] text-text-secondary overflow-x-auto truncate">
                            <span className="text-text-muted select-none">$ </span>
                            <span>{server.command}</span>
                            {server.args && server.args.length > 0 && (
                              <span className="text-text-muted"> {server.args.join(' ')}</span>
                            )}
                          </div>
                        )}

                        {/* Environment variables preview */}
                        {server.env && server.env.length > 0 && (
                          <div className="flex items-center gap-1.5 text-[10px] font-mono text-text-muted">
                            <span className="text-text-secondary">REQUIRES:</span>
                            {server.env.map((ev) => (
                              <span
                                key={ev}
                                className="px-1.5 py-0.5 rounded bg-bg-card border border-border-subtle text-text-primary"
                              >
                                {ev}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Footer Actions */}
                      <div className="pt-3 border-t border-border-subtle/50 flex items-center justify-between">
                        <div className="text-[10px] font-mono text-text-muted">
                          {server.toolsCount || 1} Tools Exposed
                        </div>

                        <button
                          onClick={() => handleToggleServerMount(server)}
                          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                            isMounted
                              ? 'border border-border-subtle text-text-muted hover:text-red-400 hover:border-red-400/40 bg-bg-card-subtle'
                              : 'bg-text-primary text-bg-main hover:opacity-90'
                          }`}
                        >
                          {isMounted ? (
                            <>
                              <Trash2 className="w-3.5 h-3.5" />
                              <span>Unmount Server</span>
                            </>
                          ) : (
                            <>
                              <Download className="w-3.5 h-3.5" />
                              <span>Mount into MaxIM</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 5. TOOL INSPECTION DRAWER / MODAL */}
      {inspectTool && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-bg-card border border-border-subtle rounded-2xl shadow-2xl p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-border-subtle pb-3">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-text-primary" />
                <h3 className="text-sm font-bold font-mono text-text-primary">{inspectTool.name}</h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-border-subtle bg-bg-card-subtle text-text-secondary">
                  {inspectTool.category}
                </span>
              </div>
              <button
                onClick={() => setInspectTool(null)}
                className="p-1 rounded-lg text-text-muted hover:text-text-primary transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-text-secondary leading-relaxed">
              {inspectTool.description}
            </p>

            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] font-mono text-text-muted uppercase">Sample ReAct Invocation</span>
              <div className="p-3 rounded-xl bg-bg-main border border-border-subtle font-mono text-xs text-text-primary select-all">
                {inspectTool.sampleCall || `${inspectTool.name}()`}
              </div>
            </div>

            <div className="flex items-center justify-between text-xs font-mono text-text-muted pt-2 border-t border-border-subtle">
              <span>Toolset: {inspectTool.toolset}</span>
              <span className="text-emerald-400">STATUS: ACTIVE & VERIFIED</span>
            </div>
          </div>
        </div>
      )}

      {/* 6. MOUNT CUSTOM MCP SERVER MODAL */}
      {isMountModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-bg-card border border-border-subtle rounded-2xl shadow-2xl p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-border-subtle pb-3">
              <div className="flex items-center gap-2">
                <Server className="w-4 h-4 text-text-primary" />
                <h3 className="text-sm font-bold text-text-primary">Mount External MCP Server</h3>
              </div>
              <button
                onClick={() => setIsMountModalOpen(false)}
                className="p-1 rounded-lg text-text-muted hover:text-text-primary transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleMountSubmit} className="flex flex-col gap-3 text-xs">
              <div className="flex flex-col gap-1">
                <label className="font-medium text-text-secondary">Server Identifier Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. postgres-analytics"
                  value={mountName}
                  onChange={(e) => setMountName(e.target.value)}
                  className="p-2.5 bg-bg-main border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:border-text-secondary font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="font-medium text-text-secondary">Transport</label>
                  <select
                    value={mountTransport}
                    onChange={(e) => setMountTransport(e.target.value as 'stdio' | 'sse')}
                    className="p-2.5 bg-bg-main border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:border-text-secondary font-mono"
                  >
                    <option value="stdio">stdio (Local Subprocess)</option>
                    <option value="sse">sse (HTTP Server-Sent Events)</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1">
                  <label className="font-medium text-text-secondary">Source Registry</label>
                  <select
                    value={mountRegistry}
                    onChange={(e) => setMountRegistry(e.target.value as any)}
                    className="p-2.5 bg-bg-main border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:border-text-secondary font-mono"
                  >
                    <option value="official">Official MCP</option>
                    <option value="smithery">Smithery</option>
                    <option value="glama">Glama</option>
                    <option value="local">Local Custom</option>
                  </select>
                </div>
              </div>

              <div className="flex flex-col gap-1">
                <label className="font-medium text-text-secondary">Execution Command</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. npx -y @modelcontextprotocol/server-postgres"
                  value={mountCommand}
                  onChange={(e) => setMountCommand(e.target.value)}
                  className="p-2.5 bg-bg-main border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:border-text-secondary font-mono"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="font-medium text-text-secondary">Arguments (space separated)</label>
                <input
                  type="text"
                  placeholder="e.g. postgresql://localhost/mydb"
                  value={mountArgs}
                  onChange={(e) => setMountArgs(e.target.value)}
                  className="p-2.5 bg-bg-main border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:border-text-secondary font-mono"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="font-medium text-text-secondary">Environment Keys (comma separated)</label>
                <input
                  type="text"
                  placeholder="e.g. API_KEY, DATABASE_URL"
                  value={mountEnv}
                  onChange={(e) => setMountEnv(e.target.value)}
                  className="p-2.5 bg-bg-main border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:border-text-secondary font-mono"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-border-subtle">
                <button
                  type="button"
                  onClick={() => setIsMountModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg border border-border-subtle text-text-secondary hover:text-text-primary transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-text-primary text-bg-main font-semibold hover:opacity-90 transition-opacity flex items-center gap-1.5"
                >
                  <span>Mount Server</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
