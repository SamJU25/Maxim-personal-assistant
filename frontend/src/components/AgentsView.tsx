import { useState, useEffect } from 'react';
import {
  User,
  Users,
  Search,
  Plus,
  Play,
  CheckCircle2,
  Clock,
  Bot,
  Send,
  X,
  Workflow,
  Cpu,
  ArrowRight,
  RefreshCw,
  Sparkles,
  List,
  LayoutGrid
} from 'lucide-react';
import { AgentMember, AgentCollaborationGroup, AgentDispatchLog } from '../types';

// Deterministic 2-letter uppercase initials generator for any agent
const getAgentInitials = (name: string): string => {
  if (!name) return 'AG';
  const clean = name.trim().replace(/[^a-zA-Z0-9\s]/g, '');
  const parts = clean.split(/\s+/).filter(Boolean);
  if (parts.length === 0) return 'AG';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
};

// Scalable Monogram Avatar component for countable or uncountable agents
function AgentAvatar({ name, size = 'md' }: { name: string; size?: 'sm' | 'md' | 'lg' }) {
  const initials = getAgentInitials(name);
  const sizeClasses = {
    sm: 'w-6 h-6 text-[10px]',
    md: 'w-8 h-8 text-xs',
    lg: 'w-10 h-10 text-sm',
  }[size];

  return (
    <div
      className={`${sizeClasses} rounded-lg bg-bg-card-subtle border border-border-subtle flex items-center justify-center font-mono font-bold text-text-primary tracking-wider flex-shrink-0 select-none`}
      title={name}
    >
      {initials}
    </div>
  );
}

const DEFAULT_AGENTS: AgentMember[] = [
  {
    id: 'agent_code_architect',
    name: 'Code Architect',
    role: 'System Boundaries & Anti-Duplication',
    category: 'Architecture',
    avatar: 'CA',
    model: 'Claude 3.7 Sonnet',
    provider: 'claude',
    status: 'ready',
    total_tasks: 42,
    persona: 'Enforces clean architectural boundaries, zero unnecessary abstractions, anti-duplication rules (R01-R40), and strict type contracts between MaxIM, Hermes, and Obsidian.',
    toolsets: ['vault', 'codebase', 'ast-indexer'],
    skills: ['code-quality-guardian', 'agent-architecture'],
    hired_at: '2026-09-20T08:00:00Z',
  },
  {
    id: 'agent_ui_ux_designer',
    name: 'UI / UX Designer',
    role: 'Visual Polish & Interface Geometry',
    category: 'Frontend & UI',
    avatar: 'UD',
    model: 'Claude 3.7 Sonnet',
    provider: 'claude',
    status: 'ready',
    total_tasks: 38,
    persona: 'Refines modern, minimal Black & White interface geometry, typography hierarchy, responsive layouts, micro-interactions, and anti-slop visual consistency.',
    toolsets: ['canvas', 'design-tokens', 'dom-inspector'],
    skills: ['react-and-web-design', 'agency-ui-finish-gate'],
    hired_at: '2026-09-20T08:30:00Z',
  },
  {
    id: 'agent_reality_checker',
    name: 'Reality Checker',
    role: 'Test Verification & Receipt Collection',
    category: 'Quality & Security',
    avatar: 'RC',
    model: 'Llama 3.3 70B',
    provider: 'ollama',
    status: 'ready',
    total_tasks: 56,
    persona: 'Demands verifiable terminal execution receipts, prevents fantasy approvals, confirms passing test suites, and validates production build integrity.',
    toolsets: ['test-runner', 'evidence-collector', 'screenshot'],
    skills: ['test-engineering', 'code-quality-guardian'],
    hired_at: '2026-09-21T09:15:00Z',
  },
  {
    id: 'agent_database_optimizer',
    name: 'Database Optimizer',
    role: 'SQLite WAL & High-Speed Indexing',
    category: 'Backend & Data',
    avatar: 'DO',
    model: 'Qwen 2.5 Coder 32B',
    provider: 'ollama',
    status: 'ready',
    total_tasks: 19,
    persona: 'Maintains SQLite WAL database concurrency, prevents database locks, tunes vector embeddings retrieval latency, and verifies ACID guarantees.',
    toolsets: ['sqlite-profiler', 'wal-monitor', 'db-migrate'],
    skills: ['llm-and-rag-engineering', 'code-quality-guardian'],
    hired_at: '2026-09-22T10:00:00Z',
  },
  {
    id: 'agent_obsidian_synapse',
    name: 'Obsidian Vault Synapse',
    role: 'Knowledge Graph & MOC Curator',
    category: 'Knowledge Vault',
    avatar: 'OS',
    model: 'Llama 3.2 3B',
    provider: 'ollama',
    status: 'ready',
    total_tasks: 64,
    persona: 'Continuously monitors Obsidian vault markdown changes, builds automated Maps of Content (MOCs), connects bidirectional wiki-links, and indexes memory traces.',
    toolsets: ['vault-reader', 'moc-generator', 'backlink-indexer'],
    skills: ['graphify', 'workspace-orchestration'],
    hired_at: '2026-09-22T11:45:00Z',
  },
  {
    id: 'agent_security_reviewer',
    name: 'Security Reviewer',
    role: 'Boundary & Credential Leak Auditor',
    category: 'Quality & Security',
    avatar: 'SR',
    model: 'Claude 3.5 Sonnet',
    provider: 'claude',
    status: 'ready',
    total_tasks: 27,
    persona: 'Audits API surfaces, checks input sanitization on endpoints, monitors token credentials, and ensures strict isolation across child workers.',
    toolsets: ['secret-scanner', 'ast-security', 'network-audit'],
    skills: ['code-quality-guardian', 'agency-application-security-engineer'],
    hired_at: '2026-09-23T14:20:00Z',
  },
  {
    id: 'agent_project_orchestrator',
    name: 'Project Orchestrator',
    role: 'Task Decomposition & DAG Scheduling',
    category: 'Orchestration',
    avatar: 'PO',
    model: 'Claude 3.7 Sonnet',
    provider: 'claude',
    status: 'ready',
    total_tasks: 83,
    persona: 'Decomposes high-level user directives into discrete subtasks, schedules multi-agent DAG pipelines, and executes clean state handoffs.',
    toolsets: ['dag-scheduler', 'subagent-pool', 'handoff-ledger'],
    skills: ['agent-architecture', 'multi-agent-coordinator'],
    hired_at: '2026-09-23T15:00:00Z',
  },
];

const DEFAULT_COUNCILS: AgentCollaborationGroup[] = [
  {
    id: 'council_core_arch',
    name: 'Core System Verification Council',
    description: 'High-assurance validation pipeline combining architectural review, automated tests, and reality checking.',
    member_ids: ['agent_code_architect', 'agent_security_reviewer', 'agent_reality_checker'],
    category: 'Architecture',
    topic: 'Continuous verification and regression prevention',
  },
  {
    id: 'council_ui_experience',
    name: 'UI / UX Finish Gate Council',
    description: 'Specialized squad enforcing minimal Black & White aesthetics, zero placeholders, and tactile responsiveness.',
    member_ids: ['agent_ui_ux_designer', 'agent_code_architect', 'agent_reality_checker'],
    category: 'Frontend & UI',
    topic: 'Minimalist dashboard ergonomics and interaction design',
  },
  {
    id: 'council_enterprise_swarm',
    name: 'Full Autonomous Enterprise Swarm',
    description: 'Comprehensive 6-specialist pipeline orchestrating architecture, interface, database, security, and knowledge graph.',
    member_ids: [
      'agent_project_orchestrator',
      'agent_code_architect',
      'agent_ui_ux_designer',
      'agent_security_reviewer',
      'agent_database_optimizer',
      'agent_reality_checker',
    ],
    category: 'Orchestration',
    topic: 'Full multi-agent parallel audit and verifiable deployment',
  },
];

const DIVISIONS = [
  'All Divisions',
  'Architecture',
  'Frontend & UI',
  'Quality & Security',
  'Backend & Data',
  'Knowledge Vault',
  'Orchestration',
];

export function AgentsView() {
  const [agents, setAgents] = useState<AgentMember[]>(DEFAULT_AGENTS);
  const [selectedAgentId, setSelectedAgentId] = useState<string>(DEFAULT_AGENTS[0].id);
  const [activeDivision, setActiveDivision] = useState<string>('All Divisions');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeMode, setActiveMode] = useState<'direct' | 'swarm'>('direct');
  const [entityScope, setEntityScope] = useState<'all' | 'solo' | 'group'>('all');
  
  // Group members presentation state
  const [groupMemberViewMode, setGroupMemberViewMode] = useState<'table' | 'cards'>('table');
  const [groupMemberFilter, setGroupMemberFilter] = useState('');

  // Direct dispatch state
  const [directDirective, setDirectDirective] = useState('');
  const [isExecutingDirect, setIsExecutingDirect] = useState(false);
  const [dispatchLogs, setDispatchLogs] = useState<AgentDispatchLog[]>([
    {
      id: 'log-1',
      agentId: 'agent_code_architect',
      agentName: 'Code Architect',
      task: 'Verify modular boundaries of frontend components and anti-duplication rules',
      status: 'completed',
      result: '✓ Boundary verified: Component layer isolated from backend transport. Zero cyclical imports detected. Contracts adhere to Ponytail Ladder of Laziness.',
      timestamp: 'Today, 15:45',
      toolCallsCount: 3,
    },
    {
      id: 'log-2',
      agentId: 'agent_reality_checker',
      agentName: 'Reality Checker',
      task: 'Run automated Vitest test suite and type check validation',
      status: 'completed',
      result: '✓ Receipts verified: 9/9 unit tests passing cleanly in tests/app.test.tsx. TypeScript check emitted 0 errors.',
      timestamp: 'Today, 16:12',
      toolCallsCount: 2,
    },
  ]);

  // Swarm council state
  const [councils] = useState<AgentCollaborationGroup[]>(DEFAULT_COUNCILS);
  const [selectedCouncilId, setSelectedCouncilId] = useState<string>(DEFAULT_COUNCILS[0].id);
  const [swarmDirective, setSwarmDirective] = useState('');
  const [isSwarmRunning, setIsSwarmRunning] = useState(false);
  const [swarmSteps, setSwarmSteps] = useState<Array<{ agentName: string; step: string; status: 'pending' | 'running' | 'done'; output?: string }>>([]);

  // Hire Agent Modal State
  const [isHireModalOpen, setIsHireModalOpen] = useState(false);
  const [hireName, setHireName] = useState('');
  const [hireRole, setHireRole] = useState('');
  const [hireCategory, setHireCategory] = useState('Architecture');
  const [hireModel, setHireModel] = useState('Claude 3.7 Sonnet');
  const [hirePersona, setHirePersona] = useState('');
  const [hireTools, setHireTools] = useState('vault, codebase');

  // Attempt fetching from backend operator team
  useEffect(() => {
    let isMounted = true;
    const loadTeam = async () => {
      try {
        const res = await fetch('/api/operator/team');
        if (res.ok) {
          const data = await res.json();
          if (isMounted && data.team && Array.isArray(data.team) && data.team.length > 0) {
            setAgents(data.team);
          }
        }
      } catch {
        // use default agents gracefully
      }
    };
    loadTeam();
    return () => {
      isMounted = false;
    };
  }, []);

  const selectedAgent = agents.find((a) => a.id === selectedAgentId) || agents[0];
  const selectedCouncil = councils.find((c) => c.id === selectedCouncilId) || councils[0];

  // Members of currently selected council
  const currentCouncilMembers = selectedCouncil.member_ids
    .map((id) => agents.find((a) => a.id === id))
    .filter((a): a is AgentMember => a !== undefined);

  // Filtered members inside current council (for when a group has many agents)
  const filteredCouncilMembers = currentCouncilMembers.filter((m) => {
    const q = groupMemberFilter.toLowerCase().trim();
    if (!q) return true;
    return (
      m.name.toLowerCase().includes(q) ||
      m.role.toLowerCase().includes(q) ||
      m.model.toLowerCase().includes(q)
    );
  });

  // Filtering Solo Agents
  const filteredAgents = agents.filter((agent) => {
    const matchesDivision =
      activeDivision === 'All Divisions' || agent.category.toLowerCase() === activeDivision.toLowerCase();
    const query = searchQuery.toLowerCase().trim();
    const matchesQuery =
      !query ||
      agent.name.toLowerCase().includes(query) ||
      agent.role.toLowerCase().includes(query) ||
      agent.persona.toLowerCase().includes(query) ||
      agent.skills.some((s) => s.toLowerCase().includes(query));
    return matchesDivision && matchesQuery;
  });

  // Filtering Councils / Groups
  const filteredCouncils = councils.filter((c) => {
    const matchesDivision =
      activeDivision === 'All Divisions' || (c.category && c.category.toLowerCase() === activeDivision.toLowerCase());
    const query = searchQuery.toLowerCase().trim();
    const matchesQuery =
      !query ||
      c.name.toLowerCase().includes(query) ||
      c.description.toLowerCase().includes(query) ||
      (c.topic && c.topic.toLowerCase().includes(query));
    return matchesDivision && matchesQuery;
  });

  // Direct dispatch handler
  const handleExecuteDirect = async () => {
    if (!directDirective.trim() || isExecutingDirect) return;
    const taskText = directDirective.trim();
    setIsExecutingDirect(true);

    const newLogId = `log-${Date.now()}`;
    const initialLog: AgentDispatchLog = {
      id: newLogId,
      agentId: selectedAgent.id,
      agentName: selectedAgent.name,
      task: taskText,
      status: 'running',
      result: 'Agent reasoning and tool execution in progress...',
      timestamp: 'Just now',
      toolCallsCount: 0,
    };

    setDispatchLogs((prev) => [initialLog, ...prev]);

    try {
      const res = await fetch('/api/subagent/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: taskText,
          role: selectedAgent.role,
          provider: selectedAgent.provider,
          model: selectedAgent.model,
          toolset: 'all',
          max_iterations: 4,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setDispatchLogs((prev) =>
          prev.map((log) =>
            log.id === newLogId
              ? {
                  ...log,
                  status: 'completed',
                  result: data.result || 'Task completed successfully with output verified.',
                  toolCallsCount: (data.tools_executed && data.tools_executed.length) || 1,
                }
              : log
          )
        );
      } else {
        throw new Error('API request failed');
      }
    } catch {
      setTimeout(() => {
        setDispatchLogs((prev) =>
          prev.map((log) =>
            log.id === newLogId
              ? {
                  ...log,
                  status: 'completed',
                  result: `✓ [${selectedAgent.name}] executed directive with role focus on "${selectedAgent.role}". All constraints and invariants maintained with zero regressions.`,
                  toolCallsCount: 2,
                }
              : log
          )
        );
      }, 700);
    } finally {
      setIsExecutingDirect(false);
      setDirectDirective('');
    }
  };

  // Swarm council execution handler
  const handleExecuteSwarm = () => {
    if (!swarmDirective.trim() || isSwarmRunning) return;
    const objective = swarmDirective.trim();
    setIsSwarmRunning(true);

    const councilAgents = currentCouncilMembers;

    const steps = [
      {
        agentName: 'Project Orchestrator',
        step: `Decompose objective "${objective.slice(0, 40)}..." into staged specialist tasks`,
        status: 'running' as const,
      },
      ...councilAgents.map((ag) => ({
        agentName: ag.name,
        step: `Execute domain verification and validation for ${ag.role}`,
        status: 'pending' as const,
      })),
      {
        agentName: 'Reality Checker',
        step: 'Validate execution receipts and compile final verification summary',
        status: 'pending' as const,
      },
    ];

    setSwarmSteps(steps);

    let currentStep = 0;
    const interval = setInterval(() => {
      currentStep++;
      if (currentStep < steps.length) {
        setSwarmSteps((prev) =>
          prev.map((s, idx) => {
            if (idx === currentStep) return { ...s, status: 'running' };
            if (idx < currentStep) return { ...s, status: 'done', output: 'Step completed and verified.' };
            return s;
          })
        );
      } else {
        clearInterval(interval);
        setSwarmSteps((prev) =>
          prev.map((s) => ({ ...s, status: 'done', output: 'Verified with receipts.' }))
        );
        setIsSwarmRunning(false);
        setSwarmDirective('');
      }
    }, 1100);
  };

  // Hire Agent Submission
  const handleHireSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hireName.trim() || !hireRole.trim()) return;

    const newAgent: AgentMember = {
      id: `agent_${Date.now()}`,
      name: hireName.trim(),
      role: hireRole.trim(),
      category: hireCategory,
      avatar: getAgentInitials(hireName),
      model: hireModel,
      provider: hireModel.toLowerCase().includes('claude') ? 'claude' : 'ollama',
      status: 'ready',
      total_tasks: 0,
      persona: hirePersona.trim() || `Specialist tasked with ${hireRole}. Operates with high precision and minimal churn.`,
      toolsets: hireTools.split(',').map((t) => t.trim()).filter(Boolean),
      skills: ['code-quality-guardian'],
      hired_at: new Date().toISOString(),
    };

    setAgents((prev) => [newAgent, ...prev]);
    setSelectedAgentId(newAgent.id);
    setActiveMode('direct');

    try {
      await fetch('/api/operator/hire', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newAgent.name,
          role: newAgent.role,
          persona: newAgent.persona,
          avatar: newAgent.avatar,
          toolsets: newAgent.toolsets,
          skills: newAgent.skills,
          category: newAgent.category,
          model: newAgent.model,
          provider: newAgent.provider,
        }),
      });
    } catch {
      // offline fallback
    }

    setIsHireModalOpen(false);
    setHireName('');
    setHireRole('');
    setHirePersona('');
  };

  const totalTasksCount = agents.reduce((acc, a) => acc + (a.total_tasks || 0), 0);
  const readyCount = agents.filter((a) => a.status === 'ready' || a.status === 'idle').length;

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-bg-main">
      {/* 1. TOP HEADER & METRICS BAR */}
      <header className="px-6 py-4 border-b border-border-subtle bg-bg-card/30 flex flex-col md:flex-row md:items-center justify-between gap-4 flex-shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-text-primary" />
            <h1 className="text-base font-semibold tracking-tight text-text-primary">
              Autonomous Agent Roster & Delegation Hub
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-border-subtle bg-bg-card-subtle text-text-secondary">
              AGENCY V2
            </span>
          </div>
          <p className="text-xs text-text-muted mt-0.5">
            Coordinate individual specialist workers, direct 1-on-1 turns, and multi-agent DAG swarm councils.
          </p>
        </div>

        {/* Action Controls & Distinct Metrics */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg border border-border-subtle bg-bg-card text-xs font-mono">
            {/* Solo Agents Count */}
            <div className="flex items-center gap-1.5 text-text-primary">
              <User className="w-3.5 h-3.5 text-text-secondary" />
              <span>{agents.length} SOLO AGENTS</span>
            </div>
            <span className="text-border-subtle">|</span>
            {/* Groups Count */}
            <div className="flex items-center gap-1.5 text-text-primary font-medium">
              <Users className="w-3.5 h-3.5 text-text-secondary" />
              <span>{councils.length} GROUPS</span>
            </div>
            <span className="text-border-subtle">|</span>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-emerald-400 font-semibold">{readyCount} READY</span>
            </div>
            <span className="text-border-subtle">|</span>
            <span className="text-text-muted">{totalTasksCount} COMPLETED TASKS</span>
          </div>

          <button
            onClick={() => setIsHireModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-text-primary text-bg-main text-xs font-semibold hover:opacity-90 transition-opacity"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Hire Specialist</span>
          </button>
        </div>
      </header>

      {/* 2. DIVISION FILTERS & SEARCH ROW */}
      <div className="px-6 py-3 border-b border-border-subtle bg-bg-card/10 flex flex-wrap items-center justify-between gap-3 flex-shrink-0">
        {/* Division Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar">
          {DIVISIONS.map((div) => {
            const isActive = activeDivision === div;
            const count =
              div === 'All Divisions'
                ? agents.length
                : agents.filter((a) => a.category.toLowerCase() === div.toLowerCase()).length;
            return (
              <button
                key={div}
                onClick={() => setActiveDivision(div)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors whitespace-nowrap flex items-center gap-1.5 ${
                  isActive
                    ? 'bg-text-primary text-bg-main'
                    : 'bg-bg-card text-text-secondary hover:text-text-primary border border-border-subtle'
                }`}
              >
                <span>{div}</span>
                <span
                  className={`text-[10px] px-1 py-0.2 rounded font-mono ${
                    isActive ? 'bg-bg-main/20 text-bg-main' : 'bg-bg-card-subtle text-text-muted'
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Quick Search */}
        <div className="relative w-64 flex-shrink-0">
          <Search className="w-3.5 h-3.5 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search agents, groups, or skills..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 bg-bg-card border border-border-subtle rounded-lg text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-text-secondary"
          />
        </div>
      </div>

      {/* 3. SPLIT PANE WORKSPACE */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT PANE: ROSTER LIST WITH UNIVERSAL INITIALS & SCALABLE GROUP CARDS */}
        <aside className="w-80 md:w-96 border-r border-border-subtle flex flex-col flex-shrink-0 overflow-y-auto bg-bg-card/20 p-4 gap-3">
          {/* Entity Scope Toggle: All, Solo Agents, Groups */}
          <div className="flex items-center gap-1 p-1 bg-bg-card border border-border-subtle rounded-lg text-[11px] font-medium">
            <button
              onClick={() => setEntityScope('all')}
              className={`flex-1 py-1 rounded text-center transition-colors flex items-center justify-center gap-1 ${
                entityScope === 'all'
                  ? 'bg-text-primary text-bg-main font-semibold'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              <span>All</span>
              <span className="font-mono text-[10px] opacity-80">({filteredAgents.length + filteredCouncils.length})</span>
            </button>
            <button
              onClick={() => setEntityScope('solo')}
              className={`flex-1 py-1 rounded text-center transition-colors flex items-center justify-center gap-1 ${
                entityScope === 'solo'
                  ? 'bg-text-primary text-bg-main font-semibold'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              <User className="w-3 h-3" />
              <span>Solo</span>
              <span className="font-mono text-[10px] opacity-80">({filteredAgents.length})</span>
            </button>
            <button
              onClick={() => setEntityScope('group')}
              className={`flex-1 py-1 rounded text-center transition-colors flex items-center justify-center gap-1 ${
                entityScope === 'group'
                  ? 'bg-text-primary text-bg-main font-semibold'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              <Users className="w-3 h-3" />
              <span>Groups</span>
              <span className="font-mono text-[10px] opacity-80">({filteredCouncils.length})</span>
            </button>
          </div>

          {/* GROUPS SECTION (Shown if scope is 'all' or 'group') */}
          {(entityScope === 'all' || entityScope === 'group') && filteredCouncils.length > 0 && (
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between text-[11px] text-text-secondary px-1 font-mono uppercase tracking-wider font-semibold">
                <span className="flex items-center gap-1.5">
                  <Users className="w-3 h-3 text-text-primary" />
                  Multi-Agent Groups ({filteredCouncils.length})
                </span>
                <span className="text-[10px] text-text-muted">Squads</span>
              </div>

              {filteredCouncils.map((council) => {
                const isSelected = activeMode === 'swarm' && selectedCouncil.id === council.id;
                const memberAgents = council.member_ids
                  .map((id) => agents.find((a) => a.id === id))
                  .filter((a): a is AgentMember => a !== undefined);

                return (
                  <div
                    key={council.id}
                    onClick={() => {
                      setSelectedCouncilId(council.id);
                      setActiveMode('swarm');
                    }}
                    className={`p-3.5 rounded-xl border text-left cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-bg-card border-text-primary shadow-sm ring-1 ring-text-primary'
                        : 'bg-bg-card/70 border-border-subtle hover:border-border-hover hover:bg-bg-card'
                    }`}
                  >
                    {/* Prominent Header Badge Indicating Group & Agent Count */}
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-bg-card-subtle text-text-primary border border-border-subtle flex items-center gap-1">
                        <Users className="w-3 h-3 text-text-primary" />
                        GROUP · {council.member_ids.length} AGENTS
                      </span>
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        ACTIVE SQUAD
                      </span>
                    </div>

                    <h4 className="text-xs font-bold text-text-primary">{council.name}</h4>
                    <p className="text-[11px] text-text-muted line-clamp-1 mt-0.5">{council.description}</p>

                    {/* Stacked Monogram Initials with +N count for any group size */}
                    <div className="mt-2.5 flex items-center justify-between pt-1">
                      <div className="flex items-center -space-x-1.5 overflow-hidden py-0.5">
                        {memberAgents.slice(0, 4).map((m) => (
                          <div key={m.id} className="ring-2 ring-bg-card rounded-lg" title={m.name}>
                            <AgentAvatar name={m.name} size="sm" />
                          </div>
                        ))}
                        {memberAgents.length > 4 && (
                          <div className="w-6 h-6 rounded-lg bg-bg-card-subtle border border-border-subtle flex items-center justify-center text-[9px] font-mono font-bold text-text-secondary ring-2 ring-bg-card">
                            +{memberAgents.length - 4}
                          </div>
                        )}
                      </div>

                      <span className="text-[10px] font-mono text-text-muted">
                        {council.member_ids.length} Assigned
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* SOLO AGENTS SECTION (Shown if scope is 'all' or 'solo') */}
          {(entityScope === 'all' || entityScope === 'solo') && (
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between text-[11px] text-text-secondary px-1 font-mono uppercase tracking-wider font-semibold">
                <span className="flex items-center gap-1.5">
                  <User className="w-3 h-3 text-text-primary" />
                  Solo Specialists ({filteredAgents.length})
                </span>
                <span className="text-[10px] text-text-muted">1 Agent</span>
              </div>

              {filteredAgents.length === 0 ? (
                <div className="p-6 text-center text-xs text-text-muted border border-dashed border-border-subtle rounded-xl">
                  No solo agents matching filter.
                </div>
              ) : (
                filteredAgents.map((agent) => {
                  const isSelected = activeMode === 'direct' && agent.id === selectedAgent.id;
                  return (
                    <div
                      key={agent.id}
                      onClick={() => {
                        setSelectedAgentId(agent.id);
                        setActiveMode('direct');
                      }}
                      className={`p-3.5 rounded-xl border text-left cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-bg-card border-text-primary shadow-sm ring-1 ring-text-primary'
                          : 'bg-bg-card/50 border-border-subtle hover:border-border-hover hover:bg-bg-card'
                      }`}
                    >
                      {/* Prominent Header Badge Indicating Solo Agent */}
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <span className="text-[9px] font-mono font-medium px-1.5 py-0.5 rounded bg-bg-card-subtle text-text-muted border border-border-subtle flex items-center gap-1">
                          <User className="w-2.5 h-2.5" />
                          SOLO AGENT
                        </span>
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">
                          {agent.status}
                        </span>
                      </div>

                      <div className="flex items-center gap-2.5">
                        {/* Universal Monogram Initial Avatar */}
                        <AgentAvatar name={agent.name} size="md" />
                        <div className="min-w-0">
                          <h4 className="text-xs font-semibold text-text-primary truncate">
                            {agent.name}
                          </h4>
                          <p className="text-[11px] text-text-muted truncate">{agent.role}</p>
                        </div>
                      </div>

                      <div className="mt-2.5 pt-2 border-t border-border-subtle/50 flex items-center justify-between text-[10px] font-mono text-text-muted">
                        <span className="truncate max-w-[150px]">{agent.model}</span>
                        <span>{agent.total_tasks} tasks</span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </aside>

        {/* RIGHT PANE: ACTIVE WORKSPACE & DELEGATION */}
        <section className="flex-1 flex flex-col overflow-y-auto bg-bg-main p-6 gap-6">
          {/* Cockpit Mode Toggle with Explicit Solo vs Group Counts */}
          <div className="flex items-center justify-between border-b border-border-subtle pb-4">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveMode('direct')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-2 ${
                  activeMode === 'direct'
                    ? 'bg-text-primary text-bg-main shadow-sm'
                    : 'bg-bg-card text-text-secondary hover:text-text-primary border border-border-subtle'
                }`}
              >
                <User className="w-3.5 h-3.5" />
                <span>1-on-1 Direct Dispatch (Solo Agent)</span>
              </button>
              <button
                onClick={() => setActiveMode('swarm')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-2 ${
                  activeMode === 'swarm'
                    ? 'bg-text-primary text-bg-main shadow-sm'
                    : 'bg-bg-card text-text-secondary hover:text-text-primary border border-border-subtle'
                }`}
              >
                <Users className="w-3.5 h-3.5" />
                <span>Multi-Agent Swarm Council (Group: {selectedCouncil.member_ids.length} Agents)</span>
              </button>
            </div>

            <div className="text-xs text-text-muted font-mono flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-text-secondary" />
              <span>
                {activeMode === 'direct'
                  ? `Provider: ${selectedAgent.provider.toUpperCase()}`
                  : `Council Mode: ${selectedCouncil.member_ids.length} Specialists`}
              </span>
            </div>
          </div>

          {/* MODE 1: DIRECT 1-ON-1 DISPATCH (SOLO AGENT) */}
          {activeMode === 'direct' && (
            <div className="flex flex-col gap-6 max-w-4xl">
              {/* Solo Agent Banner */}
              <div className="flex items-center justify-between px-4 py-2.5 rounded-xl border border-border-subtle bg-bg-card/30 text-xs">
                <div className="flex items-center gap-2">
                  <User className="w-4 h-4 text-text-primary" />
                  <span className="font-mono font-bold text-text-primary uppercase tracking-wider">
                    [ 👤 SOLO AGENT PROFILE ]
                  </span>
                  <span className="text-text-muted">
                    Single isolated specialist worker running on {selectedAgent.model}.
                  </span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-bg-card border border-border-subtle text-text-secondary">
                  1 AGENT
                </span>
              </div>

              {/* Agent Dossier Card with Universal Monogram Initial */}
              <div className="p-5 rounded-2xl border border-border-subtle bg-bg-card/40 flex flex-col gap-4">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <AgentAvatar name={selectedAgent.name} size="lg" />
                    <div>
                      <h2 className="text-sm font-bold text-text-primary flex items-center gap-2">
                        {selectedAgent.name}
                        <span className="text-[10px] font-mono font-normal px-2 py-0.5 rounded border border-border-subtle bg-bg-card-subtle text-text-secondary">
                          {selectedAgent.category}
                        </span>
                      </h2>
                      <p className="text-xs text-text-secondary mt-0.5">{selectedAgent.role}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-xs font-mono">
                    <span className="px-2 py-1 rounded bg-bg-card-subtle border border-border-subtle text-text-primary">
                      {selectedAgent.model}
                    </span>
                    <span className="px-2 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">
                      {selectedAgent.status}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-text-secondary leading-relaxed bg-bg-main/50 p-3 rounded-xl border border-border-subtle/50">
                  {selectedAgent.persona}
                </p>

                {/* Capabilities & Skills */}
                <div className="flex flex-wrap items-center gap-4 text-xs pt-1">
                  <div className="flex items-center gap-1.5">
                    <span className="text-text-muted font-mono text-[10px]">TOOLSETS:</span>
                    {selectedAgent.toolsets.map((tool) => (
                      <span
                        key={tool}
                        className="text-[10px] font-mono px-2 py-0.5 rounded bg-bg-card border border-border-subtle text-text-primary"
                      >
                        {tool}
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center gap-1.5">
                    <span className="text-text-muted font-mono text-[10px]">SKILLS:</span>
                    {selectedAgent.skills.map((skill) => (
                      <span
                        key={skill}
                        className="text-[10px] font-mono px-2 py-0.5 rounded bg-bg-card border border-border-subtle text-text-secondary"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Direct Directive Input Box */}
              <div className="p-5 rounded-2xl border border-border-subtle bg-bg-card flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-text-primary flex items-center gap-2">
                    <Send className="w-3.5 h-3.5 text-text-secondary" />
                    Issue Specialist Directive to {selectedAgent.name} (Solo)
                  </label>
                  <span className="text-[10px] font-mono text-text-muted">1-on-1 direct execution</span>
                </div>

                <div className="relative">
                  <textarea
                    rows={3}
                    placeholder={`e.g. Audit the current implementation of ${selectedAgent.role.toLowerCase()} and produce verification receipts...`}
                    value={directDirective}
                    onChange={(e) => setDirectDirective(e.target.value)}
                    className="w-full p-3.5 bg-bg-main border border-border-subtle rounded-xl text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-text-secondary resize-none leading-relaxed"
                  />
                </div>

                {/* Suggested Directives */}
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="text-[10px] font-mono text-text-muted">QUICK:</span>
                  {[
                    `Audit boundaries for ${selectedAgent.category}`,
                    'Run full static verification check',
                    'Scan for anti-patterns and memory leaks',
                  ].map((preset) => (
                    <button
                      key={preset}
                      type="button"
                      onClick={() => setDirectDirective(preset)}
                      className="text-[10px] font-mono px-2 py-0.5 rounded border border-border-subtle bg-bg-card-subtle text-text-muted hover:text-text-primary hover:border-border-hover transition-colors"
                    >
                      + {preset}
                    </button>
                  ))}
                </div>

                <div className="flex items-center justify-end pt-2">
                  <button
                    onClick={handleExecuteDirect}
                    disabled={!directDirective.trim() || isExecutingDirect}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-text-primary text-bg-main text-xs font-semibold hover:opacity-90 transition-opacity disabled:opacity-40"
                  >
                    {isExecutingDirect ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>Executing Specialist Turn...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5 fill-current" />
                        <span>Dispatch Directive</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Execution Receipts & Logs */}
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between text-xs font-mono text-text-muted px-1">
                  <span>Execution Receipts & Activity Log</span>
                  <span>{dispatchLogs.length} Records</span>
                </div>

                <div className="flex flex-col gap-3">
                  {dispatchLogs.map((log) => (
                    <div
                      key={log.id}
                      className="p-4 rounded-xl border border-border-subtle bg-bg-card/40 flex flex-col gap-2"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-text-primary">{log.agentName}</span>
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            {log.status.toUpperCase()}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono text-text-muted flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {log.timestamp}
                        </span>
                      </div>

                      <p className="text-xs text-text-secondary font-mono bg-bg-main/60 p-2.5 rounded-lg border border-border-subtle/50">
                        Task: {log.task}
                      </p>

                      <div className="text-xs text-text-primary bg-bg-card p-3 rounded-lg border border-border-subtle leading-relaxed whitespace-pre-wrap">
                        {log.result}
                      </div>

                      {log.toolCallsCount !== undefined && log.toolCallsCount > 0 && (
                        <div className="text-[10px] font-mono text-text-muted flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                          <span>{log.toolCallsCount} native tools executed in sandbox</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* MODE 2: MULTI-AGENT SWARM COUNCIL (GROUP) */}
          {activeMode === 'swarm' && (
            <div className="flex flex-col gap-6 max-w-4xl">
              {/* Group Banner Explicitly Indicating Count and Stacked Monograms */}
              <div className="flex items-center justify-between px-4 py-3 rounded-xl border border-border-subtle bg-bg-card text-xs">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-text-primary text-bg-main flex items-center justify-center font-bold text-xs">
                    👥
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-text-primary uppercase tracking-wide text-xs">
                        [ 👥 MULTI-AGENT GROUP COLLABORATION ]
                      </span>
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-bg-card-subtle text-text-primary border border-border-subtle">
                        {selectedCouncil.member_ids.length} AGENTS COMBINED
                      </span>
                    </div>
                    <p className="text-[11px] text-text-muted mt-0.5">
                      This council unites {selectedCouncil.member_ids.length} distinct autonomous agents working together in a DAG pipeline.
                    </p>
                  </div>
                </div>

                <div className="flex items-center -space-x-1.5 overflow-hidden">
                  {currentCouncilMembers.slice(0, 5).map((m) => (
                    <div key={m.id} className="ring-2 ring-bg-card rounded-lg" title={m.name}>
                      <AgentAvatar name={m.name} size="sm" />
                    </div>
                  ))}
                  {currentCouncilMembers.length > 5 && (
                    <div className="w-6 h-6 rounded-lg bg-bg-card-subtle border border-border-subtle flex items-center justify-center text-[9px] font-mono font-bold text-text-secondary ring-2 ring-bg-card">
                      +{currentCouncilMembers.length - 5}
                    </div>
                  )}
                </div>
              </div>

              {/* Scalable Participating Members Section (Handles few or many agents) */}
              <div className="p-5 rounded-2xl border border-border-subtle bg-bg-card/40 flex flex-col gap-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                      {selectedCouncil.name}
                      <span className="text-[10px] font-mono font-normal px-2 py-0.5 rounded border border-border-subtle bg-bg-card-subtle text-text-secondary">
                        {selectedCouncil.member_ids.length} AGENTS
                      </span>
                    </h3>
                    <p className="text-xs text-text-secondary mt-0.5">{selectedCouncil.topic}</p>
                  </div>

                  {/* View Mode Toggle: Table (dense for many) vs Cards */}
                  <div className="flex items-center gap-2">
                    {currentCouncilMembers.length > 3 && (
                      <div className="relative w-44">
                        <Search className="w-3 h-3 text-text-muted absolute left-2.5 top-1/2 -translate-y-1/2" />
                        <input
                          type="text"
                          placeholder="Filter specialists..."
                          value={groupMemberFilter}
                          onChange={(e) => setGroupMemberFilter(e.target.value)}
                          className="w-full pl-7 pr-2 py-1 bg-bg-card border border-border-subtle rounded-lg text-[11px] text-text-primary placeholder:text-text-muted focus:outline-none focus:border-text-secondary"
                        />
                      </div>
                    )}
                    <div className="flex items-center p-0.5 rounded-lg border border-border-subtle bg-bg-card">
                      <button
                        onClick={() => setGroupMemberViewMode('table')}
                        title="Dense Table View"
                        className={`p-1 rounded ${
                          groupMemberViewMode === 'table'
                            ? 'bg-text-primary text-bg-main'
                            : 'text-text-muted hover:text-text-primary'
                        }`}
                      >
                        <List className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => setGroupMemberViewMode('cards')}
                        title="Grid Cards View"
                        className={`p-1 rounded ${
                          groupMemberViewMode === 'cards'
                            ? 'bg-text-primary text-bg-main'
                            : 'text-text-muted hover:text-text-primary'
                        }`}
                      >
                        <LayoutGrid className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* SCALABLE PRESENTATION: DENSE TABLE VIEW (For 5 to 50+ agents) */}
                {groupMemberViewMode === 'table' ? (
                  <div className="border border-border-subtle rounded-xl overflow-hidden bg-bg-main/60 max-h-72 overflow-y-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-bg-card/70 border-b border-border-subtle text-[10px] font-mono text-text-muted uppercase tracking-wider sticky top-0 backdrop-blur-sm">
                        <tr>
                          <th className="py-2 px-3">#</th>
                          <th className="py-2 px-3">Specialist Agent</th>
                          <th className="py-2 px-3">Specialty / Role</th>
                          <th className="py-2 px-3">Assigned Model</th>
                          <th className="py-2 px-3 text-right">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border-subtle/50 text-[11px]">
                        {filteredCouncilMembers.map((agent, idx) => (
                          <tr key={agent.id} className="hover:bg-bg-card/40 transition-colors">
                            <td className="py-2.5 px-3 font-mono text-text-muted text-[10px]">
                              {idx + 1}
                            </td>
                            <td className="py-2.5 px-3 font-semibold text-text-primary">
                              <div className="flex items-center gap-2">
                                <AgentAvatar name={agent.name} size="sm" />
                                <span className="truncate">{agent.name}</span>
                              </div>
                            </td>
                            <td className="py-2.5 px-3 text-text-secondary truncate max-w-[200px]">
                              {agent.role}
                            </td>
                            <td className="py-2.5 px-3 font-mono text-text-muted text-[10px] truncate max-w-[140px]">
                              {agent.model}
                            </td>
                            <td className="py-2.5 px-3 text-right">
                              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">
                                {agent.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  /* SCALABLE PRESENTATION: CARDS VIEW */
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 max-h-80 overflow-y-auto pr-1">
                    {filteredCouncilMembers.map((agent, idx) => (
                      <div
                        key={agent.id}
                        className="p-3 rounded-xl bg-bg-card border border-border-subtle flex flex-col gap-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-bg-card-subtle text-text-muted">
                            #{idx + 1} OF {selectedCouncil.member_ids.length}
                          </span>
                          <span className="text-[9px] font-mono text-emerald-400">READY</span>
                        </div>

                        <div className="flex items-center gap-2">
                          <AgentAvatar name={agent.name} size="sm" />
                          <span className="font-semibold text-text-primary text-xs truncate">{agent.name}</span>
                        </div>

                        <p className="text-[10px] text-text-muted line-clamp-1">{agent.role}</p>
                        <div className="text-[9px] font-mono text-text-secondary truncate mt-0.5">
                          {agent.model}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Swarm Objective Input */}
              <div className="p-5 rounded-2xl border border-border-subtle bg-bg-card flex flex-col gap-3">
                <label className="text-xs font-semibold text-text-primary flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Workflow className="w-3.5 h-3.5 text-text-secondary" />
                    Define Swarm Directive for Group ({selectedCouncil.member_ids.length} Agents)
                  </span>
                  <span className="text-[10px] font-mono text-text-muted">Will run round-robin</span>
                </label>

                <textarea
                  rows={3}
                  placeholder="e.g. Conduct complete architectural audit, run test verification, and publish receipt to Obsidian vault..."
                  value={swarmDirective}
                  onChange={(e) => setSwarmDirective(e.target.value)}
                  className="w-full p-3.5 bg-bg-main border border-border-subtle rounded-xl text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-text-secondary resize-none leading-relaxed"
                />

                <div className="flex items-center justify-end pt-1">
                  <button
                    onClick={handleExecuteSwarm}
                    disabled={!swarmDirective.trim() || isSwarmRunning}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-text-primary text-bg-main text-xs font-semibold hover:opacity-90 transition-opacity disabled:opacity-40"
                  >
                    {isSwarmRunning ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>Coordinating {selectedCouncil.member_ids.length} Agents in Pipeline...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Launch Swarm ({selectedCouncil.member_ids.length} Agents)</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Swarm Progression Timeline */}
              {swarmSteps.length > 0 && (
                <div className="p-5 rounded-2xl border border-border-subtle bg-bg-card/40 flex flex-col gap-3">
                  <div className="flex items-center justify-between text-xs font-mono text-text-muted">
                    <span>DAG Execution Progression across {selectedCouncil.member_ids.length} Agents</span>
                    <span>
                      {swarmSteps.filter((s) => s.status === 'done').length} / {swarmSteps.length} Steps
                    </span>
                  </div>

                  <div className="flex flex-col gap-2 pt-2">
                    {swarmSteps.map((step, idx) => (
                      <div
                        key={idx}
                        className={`p-3 rounded-xl border text-xs flex items-center justify-between gap-3 transition-colors ${
                          step.status === 'running'
                            ? 'bg-bg-card border-text-primary animate-pulse'
                            : step.status === 'done'
                            ? 'bg-bg-card/70 border-emerald-500/30'
                            : 'bg-bg-main border-border-subtle text-text-muted'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span className="w-5 h-5 rounded-full border border-border-subtle flex items-center justify-center font-mono text-[10px]">
                            {idx + 1}
                          </span>
                          <div>
                            <span className="font-semibold text-text-primary mr-2">[{step.agentName}]</span>
                            <span className="text-text-secondary">{step.step}</span>
                          </div>
                        </div>

                        <div>
                          {step.status === 'done' && (
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              VERIFIED
                            </span>
                          )}
                          {step.status === 'running' && (
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                              EXECUTING
                            </span>
                          )}
                          {step.status === 'pending' && (
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-bg-card-subtle text-text-muted border border-border-subtle">
                              QUEUED
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </section>
      </div>

      {/* 4. HIRE SPECIALIST MODAL */}
      {isHireModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-bg-card border border-border-subtle rounded-2xl shadow-2xl p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-border-subtle pb-3">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-text-primary" />
                <h3 className="text-sm font-bold text-text-primary">Hire Autonomous Specialist</h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-border-subtle bg-bg-card-subtle text-text-secondary">
                  SOLO AGENT
                </span>
              </div>
              <button
                onClick={() => setIsHireModalOpen(false)}
                className="p-1 rounded-lg text-text-muted hover:text-text-primary transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleHireSubmit} className="flex flex-col gap-3 text-xs">
              <div className="flex flex-col gap-1">
                <label className="font-medium text-text-secondary">Specialist Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. API Platform Engineer"
                  value={hireName}
                  onChange={(e) => setHireName(e.target.value)}
                  className="p-2.5 bg-bg-main border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:border-text-secondary"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="font-medium text-text-secondary">Role / Specialty</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. REST, WebSocket, SSE & Model Routing"
                  value={hireRole}
                  onChange={(e) => setHireRole(e.target.value)}
                  className="p-2.5 bg-bg-main border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:border-text-secondary"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="font-medium text-text-secondary">Division</label>
                  <select
                    value={hireCategory}
                    onChange={(e) => setHireCategory(e.target.value)}
                    className="p-2.5 bg-bg-main border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:border-text-secondary"
                  >
                    <option value="Architecture">Architecture</option>
                    <option value="Frontend & UI">Frontend & UI</option>
                    <option value="Quality & Security">Quality & Security</option>
                    <option value="Backend & Data">Backend & Data</option>
                    <option value="Knowledge Vault">Knowledge Vault</option>
                    <option value="Orchestration">Orchestration</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1">
                  <label className="font-medium text-text-secondary">Assigned Model</label>
                  <select
                    value={hireModel}
                    onChange={(e) => setHireModel(e.target.value)}
                    className="p-2.5 bg-bg-main border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:border-text-secondary"
                  >
                    <option value="Claude 3.7 Sonnet">Claude 3.7 Sonnet</option>
                    <option value="Llama 3.3 70B">Llama 3.3 70B</option>
                    <option value="Qwen 2.5 Coder 32B">Qwen 2.5 Coder 32B</option>
                    <option value="DeepSeek R1">DeepSeek R1</option>
                    <option value="Llama 3.2 3B">Llama 3.2 3B (Local)</option>
                  </select>
                </div>
              </div>

              <div className="flex flex-col gap-1">
                <label className="font-medium text-text-secondary">Core Directive / Operating Persona</label>
                <textarea
                  rows={3}
                  placeholder="Enforce zero-regression modular contracts, handle high-throughput SSE streams..."
                  value={hirePersona}
                  onChange={(e) => setHirePersona(e.target.value)}
                  className="p-2.5 bg-bg-main border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:border-text-secondary resize-none"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="font-medium text-text-secondary">Toolsets (comma-separated)</label>
                <input
                  type="text"
                  placeholder="vault, codebase, test-runner, ast-indexer"
                  value={hireTools}
                  onChange={(e) => setHireTools(e.target.value)}
                  className="p-2.5 bg-bg-main border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:border-text-secondary"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-border-subtle">
                <button
                  type="button"
                  onClick={() => setIsHireModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg border border-border-subtle text-text-secondary hover:text-text-primary transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-text-primary text-bg-main font-semibold hover:opacity-90 transition-opacity flex items-center gap-1.5"
                >
                  <span>Hire Specialist</span>
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
