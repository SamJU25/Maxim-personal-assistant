import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act, fireEvent } from '@testing-library/react';
import App from '../src/App';
import { TelegramChat } from '../src/components/TelegramChat';

describe('MaxIM App Frontend - Phase 1 Verification', () => {
  beforeEach(() => {
    // Mock global fetch for health and telemetry
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/health')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ active_provider: 'ollama', status: 'healthy' }),
        });
      }
      if (url.includes('/api/hardware/telemetry')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            cpu_percent: 24.5,
            cpu_cores: 16,
            ram_total_gb: 32.0,
            ram_used_gb: 12.4,
            ram_free_gb: 19.6,
            ram_percent: 38.7,
            ollama_online: true,
          }),
        });
      }
      if (url.includes('/api/providers')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            active_provider: 'unsloth',
            connected_cloud_providers: [
              {
                provider: 'anthropic',
                name: 'Anthropic Claude',
                model_name: 'claude-3.5-sonnet',
                base_url: 'https://api.anthropic.com/v1',
                is_cloud: true,
              },
            ],
            providers: {},
          }),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    }) as any;
  });

  it('renders MaxIM header, badge, and navigation tabs', async () => {
    await act(async () => {
      render(<App />);
    });
    expect(screen.getByText('MaxIM')).toBeInTheDocument();
    expect(screen.getByText('v2.0 Native')).toBeInTheDocument();
    expect(screen.getByText('ONLINE')).toBeInTheDocument();

    // Verify all 7 top-level navigation items
    expect(screen.getByRole('button', { name: /home/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /memory/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /graph/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /agents/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /skills/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /connections/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /settings/i })).toBeInTheDocument();
  });

  it('renders Left Column: Date/Time HUD, Visual Uplink, and System Telemetry', async () => {
    await act(async () => {
      render(<App />);
    });

    // Date & Time HUD
    expect(screen.getByText('System Clock')).toBeInTheDocument();
    expect(screen.getByText('LIVE')).toBeInTheDocument();

    // Visual Uplink
    expect(screen.getByText('Perception Feed')).toBeInTheDocument();
    expect(screen.getByText('STANDBY')).toBeInTheDocument();
    expect(screen.getByText('Click to Engage Uplink')).toBeInTheDocument();

    // System Telemetry
    expect(screen.getByText('System Telemetry')).toBeInTheDocument();
    expect(screen.getByText('CPU Load')).toBeInTheDocument();
    expect(screen.getByText('Memory (RAM)')).toBeInTheDocument();
    expect(screen.getByText(/Ollama Engine:/i)).toBeInTheDocument();
  });

  it('opens and closes the Visual Uplink perception modal', async () => {
    await act(async () => {
      render(<App />);
    });

    // Click on standby card to open modal
    const uplinkTrigger = screen.getByText('Click to Engage Uplink');
    await act(async () => {
      fireEvent.click(uplinkTrigger);
    });

    expect(screen.getByText('Engage Visual Perception')).toBeInTheDocument();
    expect(screen.getByText('Camera Feed')).toBeInTheDocument();
    expect(screen.getByText('Screen Share')).toBeInTheDocument();

    // Close the modal
    const buttons = screen.getAllByRole('button');
    const xButton = buttons.find((btn) => btn.querySelector('svg.lucide-x'));
    if (xButton) {
      await act(async () => {
        fireEvent.click(xButton);
      });
      expect(screen.queryByText('Engage Visual Perception')).not.toBeInTheDocument();
    }
  });

  it('toggles Black & White theme mode', async () => {
    await act(async () => {
      render(<App />);
    });

    const lightButton = screen.getByRole('button', { name: /switch to light mode/i });
    const darkButton = screen.getByRole('button', { name: /switch to dark mode/i });
    expect(lightButton).toBeInTheDocument();
    expect(darkButton).toBeInTheDocument();

    // Toggle to Light mode
    await act(async () => {
      fireEvent.click(lightButton);
    });
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');

    // Toggle back to Dark mode
    await act(async () => {
      fireEvent.click(darkButton);
    });
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });

  it('renders clean chat dock on Home and is blank initially', async () => {
    await act(async () => {
      render(<App />);
    });
    expect(screen.getByPlaceholderText('Ask MaxIM or command computer use...')).toBeInTheDocument();
    expect(screen.queryByText('MaxIM ReAct Engine Online')).not.toBeInTheDocument();

    const newChatBtn = screen.getByRole('button', { name: /new chat/i });
    await act(async () => {
      fireEvent.click(newChatBtn);
    });
    expect(screen.getByPlaceholderText('Ask MaxIM or command computer use...')).toBeInTheDocument();
    expect(screen.queryByText('MaxIM ReAct Engine Online')).not.toBeInTheDocument();
  });

  it('switches views smoothly via top navigation tabs', async () => {
    await act(async () => {
      render(<App />);
    });

    // Switch to Memory view
    const memoryTab = screen.getByRole('button', { name: /memory/i });
    await act(async () => {
      fireEvent.click(memoryTab);
    });
    expect(screen.getByText(/Obsidian Knowledge & Memory Store/i)).toBeInTheDocument();

    // Switch to Graph view
    const graphTab = screen.getByRole('button', { name: /graph/i });
    await act(async () => {
      fireEvent.click(graphTab);
    });
    expect(screen.getByText(/Interactive Force-Directed Knowledge Graph/i)).toBeInTheDocument();

    // Switch back to Home view
    const homeTab = screen.getByRole('button', { name: /home/i });
    await act(async () => {
      fireEvent.click(homeTab);
    });
    expect(screen.getByText('System Clock')).toBeInTheDocument();
    expect(screen.getByText('Kai Vector Mascot')).toBeInTheDocument();
  });

  it('supports TelegramChat interactions: thinking accordion, document modal, and new chat', async () => {
    const testMessages = [
      {
        id: 'm1',
        sender: 'assistant' as const,
        content: 'Autonomous workspace ready. ReAct engine initialized with local FastMCP toolsets and 5-layer memory.',
        timestamp: '16:15',
        thinking: 'Evaluated host status: Ollama online (Llama 3.2), RAM 11.2GB/32GB, WAL database healthy. Ready for user directives.',
      },
      {
        id: 'm2',
        sender: 'assistant' as const,
        content: 'Verified architecture blueprint preview.',
        timestamp: '16:16',
        documents: [
          {
            id: 'doc-1',
            title: 'ARCHITECTURE_OVERVIEW.md',
            category: 'System Spec',
            snippet: 'MaxIM V2 architecture: Python FastAPI backend + React 19 frontend + FastMCP tool registry.',
            fullText: `# MaxIM V2 Architecture Overview\n\n- Backend: FastAPI (Python 3.12)\n- Storage: SQLite WAL mode with 5-layer memory\n- Frontend: React 19 + Tailwind CSS (B/W Minimalist)\n- Tooling: FastMCP Registry with Smithery & Glama hub discovery\n- Telemetry: Real-time CPU, RAM, and GPU VRAM tracking.`,
          },
        ],
      },
    ];

    await act(async () => {
      render(<TelegramChat initialMessages={testMessages} />);
    });

    // Expand thought process
    const thoughtButtons = screen.getAllByRole('button', { name: /thought process/i });
    expect(thoughtButtons.length).toBeGreaterThan(0);
    await act(async () => {
      fireEvent.click(thoughtButtons[0]);
    });
    expect(screen.getByText(/Evaluated host status:/i)).toBeInTheDocument();

    // Click Document preview to open Document Reader
    const docCard = screen.getByText('ARCHITECTURE_OVERVIEW.md');
    expect(docCard).toBeInTheDocument();
    await act(async () => {
      fireEvent.click(docCard);
    });
    expect(screen.getByText(/MaxIM V2 Architecture Overview/i)).toBeInTheDocument();

    // Close Document Reader
    const closeButtons = screen.getAllByRole('button');
    const xButton = closeButtons.find((btn) => btn.querySelector('svg.lucide-x'));
    if (xButton) {
      await act(async () => {
        fireEvent.click(xButton);
      });
    }

    // Click New Chat to clear
    const newChatBtn = screen.getByRole('button', { name: /new chat/i });
    await act(async () => {
      fireEvent.click(newChatBtn);
    });
    expect(screen.queryByText('Autonomous workspace ready.')).not.toBeInTheDocument();
    expect(screen.getByPlaceholderText('Ask MaxIM or command computer use...')).toBeInTheDocument();
  });

  it('supports MemoryView 5-layer overview, search, and Add Memory modal', async () => {
    await act(async () => {
      render(<App />);
    });

    // Navigate to Memory tab
    const memoryTab = screen.getByRole('button', { name: /memory/i });
    await act(async () => {
      fireEvent.click(memoryTab);
    });

    // Verify 5-layer cards
    expect(screen.getByText('Working Context')).toBeInTheDocument();
    expect(screen.getByText('Episodic Traces')).toBeInTheDocument();
    expect(screen.getByText('Semantic Knowledge')).toBeInTheDocument();
    expect(screen.getByText('Procedural Skills')).toBeInTheDocument();
    expect(screen.getByText('Obsidian Vault')).toBeInTheDocument();

    // Click "Add Memory Manually"
    const addMemoryBtn = screen.getByRole('button', { name: /add memory manually/i });
    await act(async () => {
      fireEvent.click(addMemoryBtn);
    });

    // Verify modal opens
    expect(screen.getByPlaceholderText(/e\.g\. MaxIM V2 uses local SQLite WAL mode/i)).toBeInTheDocument();

    // Fill in new memory
    const textarea = screen.getByPlaceholderText(/e\.g\. MaxIM V2 uses local SQLite WAL mode/i);
    await act(async () => {
      fireEvent.change(textarea, { target: { value: 'User requested minimal black and white dashboard design.' } });
    });

    // Submit form
    const saveBtn = screen.getByRole('button', { name: /save to memory store/i });
    await act(async () => {
      fireEvent.click(saveBtn);
    });

    // Verify optimistic addition in memory list
    expect(screen.getByText('User requested minimal black and white dashboard design.')).toBeInTheDocument();
  });

  it('supports GraphView interactive force-directed graph with semantic legend and filters', async () => {
    await act(async () => {
      render(<App />);
    });

    // Navigate to Graph tab
    const graphTab = screen.getByRole('button', { name: /graph/i });
    await act(async () => {
      fireEvent.click(graphTab);
    });

    // Verify title and semantic legend
    expect(screen.getByText('Interactive Force-Directed Knowledge Graph')).toBeInTheDocument();
    expect(screen.getAllByText('Agents').length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText('Skills').length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText('Active Session')).toBeInTheDocument();

    // Verify zoom and view controls
    expect(screen.getByTitle('Zoom In')).toBeInTheDocument();
    expect(screen.getByTitle('Zoom Out')).toBeInTheDocument();
    expect(screen.getByTitle('Reset View')).toBeInTheDocument();

    // Test filter pill click
    const agentFilterBtn = screen.getByRole('button', { name: /^agent$/i });
    await act(async () => {
      fireEvent.click(agentFilterBtn);
    });
    expect(agentFilterBtn).toBeInTheDocument();
  });

  it('supports AgentsView specialist roster, direct dispatch, swarm councils, and hire modal', async () => {
    await act(async () => {
      render(<App />);
    });

    // Navigate to Agents tab
    const agentsTab = screen.getByRole('button', { name: /agents/i });
    await act(async () => {
      fireEvent.click(agentsTab);
    });

    // Header & stats
    expect(screen.getByText('Autonomous Agent Roster & Delegation Hub')).toBeInTheDocument();
    expect(screen.getAllByText(/READY/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/COMPLETED TASKS/i)).toBeInTheDocument();

    // Specialists in roster
    expect(screen.getAllByText('Code Architect').length).toBeGreaterThan(0);
    expect(screen.getAllByText('UI / UX Designer').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Reality Checker').length).toBeGreaterThan(0);

    // Mode toggle: Direct Dispatch is active initially
    expect(screen.getByRole('button', { name: /1-on-1 direct dispatch/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Audit the current implementation/i)).toBeInTheDocument();

    // Switch to Multi-Agent Swarm Council mode
    const swarmModeBtn = screen.getByRole('button', { name: /multi-agent swarm council/i });
    await act(async () => {
      fireEvent.click(swarmModeBtn);
    });
    expect(screen.getAllByText('Core System Verification Council').length).toBeGreaterThan(0);
    expect(screen.getByPlaceholderText(/Conduct complete architectural audit/i)).toBeInTheDocument();

    // Open Hire Specialist Modal
    const hireBtn = screen.getByRole('button', { name: /hire specialist/i });
    await act(async () => {
      fireEvent.click(hireBtn);
    });
    expect(screen.getByText('Hire Autonomous Specialist')).toBeInTheDocument();

    // Fill in new specialist
    const nameInput = screen.getByPlaceholderText('e.g. API Platform Engineer');
    const roleInput = screen.getByPlaceholderText(/e\.g\. REST, WebSocket, SSE/i);
    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'API Platform Specialist' } });
      fireEvent.change(roleInput, { target: { value: 'High throughput streaming' } });
    });

    // Submit modal form
    const submitHire = screen.getAllByRole('button').find((btn) => btn.textContent?.includes('Hire Specialist') && btn.getAttribute('type') === 'submit');
    if (submitHire) {
      await act(async () => {
        fireEvent.click(submitHire);
      });
    }

    // Modal should close and specialist appears in list
    expect(screen.queryByText('Hire Autonomous Specialist')).not.toBeInTheDocument();
    expect(screen.getAllByText('API Platform Specialist').length).toBeGreaterThan(0);
  });

  it('supports SkillsView native toolsets, schema inspection, MCP marketplace, and custom mount modal', async () => {
    await act(async () => {
      render(<App />);
    });

    // Navigate to Skills tab
    const skillsTab = screen.getByRole('button', { name: /skills/i });
    await act(async () => {
      fireEvent.click(skillsTab);
    });

    // Header & counters
    expect(screen.getByText('Skills Directory & MCP Marketplace Hub')).toBeInTheDocument();
    expect(screen.getAllByText(/NATIVE TOOLS/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/MOUNTED SERVERS/i).length).toBeGreaterThan(0);

    // Native tools in grid
    expect(screen.getByText('read_vault_note')).toBeInTheDocument();
    expect(screen.getByText('execute_powershell')).toBeInTheDocument();
    expect(screen.getByText('fetch_jina_reader')).toBeInTheDocument();

    // Inspect Schema on read_vault_note
    const inspectButtons = screen.getAllByRole('button', { name: /inspect schema/i });
    expect(inspectButtons.length).toBeGreaterThan(0);
    await act(async () => {
      fireEvent.click(inspectButtons[0]);
    });

    // Verify inspection drawer
    expect(screen.getByText(/Sample ReAct Invocation/i)).toBeInTheDocument();
    expect(screen.getByText(/read_vault_note\(title="00 - LifeOS\/TELOS\.md"\)/i)).toBeInTheDocument();

    // Close inspection drawer
    const closeButtons = screen.getAllByRole('button');
    const xButton = closeButtons.find((btn) => btn.querySelector('svg.lucide-x'));
    if (xButton) {
      await act(async () => {
        fireEvent.click(xButton);
      });
    }

    // Switch to MCP Marketplace & Servers tab
    const mcpTabBtn = screen.getByRole('button', { name: /mcp marketplace & servers/i });
    await act(async () => {
      fireEvent.click(mcpTabBtn);
    });

    // Verify MCP servers
    expect(screen.getByText('filesystem')).toBeInTheDocument();
    expect(screen.getByText('sqlite')).toBeInTheDocument();
    expect(screen.getByText('brave-search')).toBeInTheDocument();

    // Open Mount MCP Server Modal
    const mountBtn = screen.getByRole('button', { name: /mount mcp server/i });
    await act(async () => {
      fireEvent.click(mountBtn);
    });
    expect(screen.getByText('Mount External MCP Server')).toBeInTheDocument();

    // Fill in custom server details
    const nameInput = screen.getByPlaceholderText('e.g. postgres-analytics');
    const cmdInput = screen.getByPlaceholderText('e.g. npx -y @modelcontextprotocol/server-postgres');
    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'redis-cache' } });
      fireEvent.change(cmdInput, { target: { value: 'npx -y @mcp/redis' } });
    });

    // Submit mount form
    const submitMount = screen.getAllByRole('button').find((btn) => btn.textContent?.includes('Mount Server') && btn.getAttribute('type') === 'submit');
    if (submitMount) {
      await act(async () => {
        fireEvent.click(submitMount);
      });
    }

    // Modal closes and new server appears
    expect(screen.queryByText('Mount External MCP Server')).not.toBeInTheDocument();
    expect(screen.getByText('redis-cache')).toBeInTheDocument();
  });

  it('supports ConnectionsView channel gateways, outbound dispatch, configuration modal, and unified inbox logs', async () => {
    await act(async () => {
      render(<App />);
    });

    // Navigate to Connections tab
    const connectionsTab = screen.getByRole('button', { name: /connections/i });
    await act(async () => {
      fireEvent.click(connectionsTab);
    });

    // Header & counters
    expect(screen.getByText('External Uplinks & Communication Gateways')).toBeInTheDocument();
    expect(screen.getAllByText(/INBOUND:/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/OUTBOUND:/i).length).toBeGreaterThan(0);

    // Channel cards
    expect(screen.getByText('Telegram Bot Gateway')).toBeInTheDocument();
    expect(screen.getByText('Discord Gateway & Webhook')).toBeInTheDocument();
    expect(screen.getByText('Slack Notification Uplink')).toBeInTheDocument();
    expect(screen.getByText('Obsidian Vault Synapse')).toBeInTheDocument();
    expect(screen.getByText('Universal JSON Webhook & Shortcuts')).toBeInTheDocument();

    // Quick Manual Dispatcher
    const dispatchInput = screen.getByPlaceholderText('Message payload to transmit remotely...');
    const transmitBtn = screen.getByRole('button', { name: /transmit/i });
    await act(async () => {
      fireEvent.change(dispatchInput, { target: { value: 'Test remote beacon packet' } });
      fireEvent.click(transmitBtn);
    });

    // Verify feedback
    expect(screen.getByText(/Dispatched cleanly to TELEGRAM/i)).toBeInTheDocument();

    // Open Configure Modal on Telegram
    const configButtons = screen.getAllByRole('button', { name: /configure/i });
    expect(configButtons.length).toBeGreaterThan(0);
    await act(async () => {
      fireEvent.click(configButtons[0]);
    });
    expect(screen.getByText(/Configure Telegram Bot Gateway/i)).toBeInTheDocument();

    // Change target and save
    const targetInput = screen.getByPlaceholderText('e.g. 928374102 or #general');
    await act(async () => {
      fireEvent.change(targetInput, { target: { value: 'chat_id: 999888111' } });
    });
    const saveBtn = screen.getByRole('button', { name: /save configuration/i });
    await act(async () => {
      fireEvent.click(saveBtn);
    });

    // Switch to Unified Inbox tab
    const inboxTabBtn = screen.getByRole('button', { name: /unified inbox & dispatch logs/i });
    await act(async () => {
      fireEvent.click(inboxTabBtn);
    });

    // Verify logs
    expect(screen.getByText('Universal Cross-Channel Ledger')).toBeInTheDocument();
    expect(screen.getByText(/Telemetry report delivered to Apple Shortcuts daemon/i)).toBeInTheDocument();
  });

  it('supports SettingsView provider gateways, custom mount modal, neural voice, personality, and privacy controls', async () => {
    await act(async () => {
      render(<App />);
    });

    // Navigate to Settings tab
    const settingsTab = screen.getByRole('button', { name: /settings/i });
    await act(async () => {
      fireEvent.click(settingsTab);
    });

    // Header & counters
    expect(screen.getByText('System Preferences & Neural Cockpit Settings')).toBeInTheDocument();
    expect(screen.getByText(/Sam \(Sovereign\)/i)).toBeInTheDocument();

    // Provider cards in models tab
    expect(screen.getAllByText('Local Ollama Engine').length).toBeGreaterThan(0);
    expect(screen.getByText('Google Gemini')).toBeInTheDocument();
    expect(screen.getByText('OpenAI ChatGPT')).toBeInTheDocument();
    expect(screen.getByText('DeepSeek AI')).toBeInTheDocument();

    // Open Custom Provider Modal
    const addCustomBtn = screen.getByRole('button', { name: /add custom provider/i });
    await act(async () => {
      fireEvent.click(addCustomBtn);
    });
    expect(screen.getByText('Register Custom OpenAI-Compatible Provider')).toBeInTheDocument();

    // Fill in custom provider details
    const provNameInput = screen.getByPlaceholderText('e.g. Local vLLM Server');
    const provUrlInput = screen.getByPlaceholderText('e.g. http://localhost:8080/v1');
    const provModelInput = screen.getByPlaceholderText('e.g. mistral-7b-instruct');
    await act(async () => {
      fireEvent.change(provNameInput, { target: { value: 'Fast vLLM Node' } });
      fireEvent.change(provUrlInput, { target: { value: 'http://localhost:9000/v1' } });
      fireEvent.change(provModelInput, { target: { value: 'mixtral-8x22b' } });
    });

    // Submit custom provider
    const mountProvBtn = screen.getByRole('button', { name: /mount provider/i });
    await act(async () => {
      fireEvent.click(mountProvBtn);
    });

    // Modal closes and new provider appears
    expect(screen.queryByText('Register Custom OpenAI-Compatible Provider')).not.toBeInTheDocument();
    expect(screen.getByText('Fast vLLM Node')).toBeInTheDocument();

    // Switch to Neural Voice & Audio tab
    const voiceTabBtn = screen.getByRole('button', { name: /neural voice & audio/i });
    await act(async () => {
      fireEvent.click(voiceTabBtn);
    });

    expect(screen.getByText('Edge-TTS Neural Voice Engine')).toBeInTheDocument();
    expect(screen.getByText('Christopher (US)')).toBeInTheDocument();
    expect(screen.getByText('Ryan (British)')).toBeInTheDocument();
    expect(screen.getByText('Pradeep (Bangla)')).toBeInTheDocument();

    // Select Ryan voice
    const ryanVoice = screen.getByText('Ryan (British)');
    await act(async () => {
      fireEvent.click(ryanVoice);
    });

    // Click Test Voice
    const testVoiceBtn = screen.getByRole('button', { name: /test voice/i });
    await act(async () => {
      fireEvent.click(testVoiceBtn);
    });

    // Switch to Personality & Initiative tab
    const personaTabBtn = screen.getByRole('button', { name: /personality & initiative/i });
    await act(async () => {
      fireEvent.click(personaTabBtn);
    });

    expect(screen.getByText('Proactive Situational Initiative')).toBeInTheDocument();
    expect(screen.getByText('Muted (Passive)')).toBeInTheDocument();
    expect(screen.getByText('Gentle (Infrequent)')).toBeInTheDocument();
    expect(screen.getByText('Balanced (Standard)')).toBeInTheDocument();
    expect(screen.getByText('Proactive (Accountability Partner)')).toBeInTheDocument();

    // Select Proactive mode
    const proactiveMode = screen.getByText('Proactive (Accountability Partner)');
    await act(async () => {
      fireEvent.click(proactiveMode);
    });

    // Save Persona
    const savePersonaBtn = screen.getByRole('button', { name: /save persona/i });
    await act(async () => {
      fireEvent.click(savePersonaBtn);
    });

    // Switch to Privacy, Hardware & Theme tab
    const sysTabBtn = screen.getByRole('button', { name: /privacy, hardware & theme/i });
    await act(async () => {
      fireEvent.click(sysTabBtn);
    });

    expect(screen.getByText('Sacred Owner Loyalty & Zero-Egress Sandbox')).toBeInTheDocument();
    expect(screen.getByText('Local Path Redaction')).toBeInTheDocument();
    expect(screen.getByText('Cockpit Display & Telemetry Polling')).toBeInTheDocument();
  });

  it('supports right column tab switching between Chat, Intelligence, and Activity', async () => {
    await act(async () => {
      render(<App />);
    });

    // Verify all 3 compact tabs exist
    expect(screen.getByRole('button', { name: /^chat$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^intelligence$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^activity$/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Ask MaxIM or command computer use...')).toBeInTheDocument();

    // Switch to Intelligence tab
    const intelBtn = screen.getByRole('button', { name: /^intelligence$/i });
    await act(async () => {
      fireEvent.click(intelBtn);
    });
    expect(screen.getByText('Executive Daily Briefing')).toBeInTheDocument();
    expect(screen.getByText('TELOS Master Objectives')).toBeInTheDocument();

    // Switch to Activity tab
    const activityBtn = screen.getByRole('button', { name: /^activity$/i });
    await act(async () => {
      fireEvent.click(activityBtn);
    });
    expect(screen.getByText('Recent System Executions')).toBeInTheDocument();
    expect(screen.getByText('Obsidian Note Captured')).toBeInTheDocument();
    expect(screen.getByText('TELOS Target Audit')).toBeInTheDocument();

    // Switch back to Chat tab
    const chatBtn = screen.getByRole('button', { name: /^chat$/i });
    await act(async () => {
      fireEvent.click(chatBtn);
    });
    expect(screen.getByPlaceholderText('Ask MaxIM or command computer use...')).toBeInTheDocument();
  });

  it('supports model selector drop-up combobox opening upwards and selecting model', async () => {
    await act(async () => {
      render(<App />);
    });

    const modelCombobox = screen.getByRole('combobox');
    expect(modelCombobox).toBeInTheDocument();
    expect(modelCombobox).toHaveAttribute('aria-expanded', 'false');

    // Click to open combobox upwards
    await act(async () => {
      fireEvent.click(modelCombobox);
    });
    expect(modelCombobox).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('listbox')).toBeInTheDocument();
    expect(screen.getByText('Select Provider & Model')).toBeInTheDocument();

    // Select Claude
    const sonnetOption = screen.getByRole('option', { name: /Claude/i });
    await act(async () => {
      fireEvent.click(sonnetOption);
    });

    // Combobox closes and trigger text updates
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    expect(screen.getByRole('combobox')).toHaveTextContent(/Claude/i);
  });
});


