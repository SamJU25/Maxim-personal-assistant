import React, { useState, useEffect, useRef } from 'react';
import {
  Network,
  Search,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  X,
} from 'lucide-react';
import { ThemeMode } from '../types';

export type NodeType = 'agent' | 'memory' | 'skill' | 'active';

export interface GraphNode {
  id: string;
  label: string;
  type: NodeType;
  group: string;
  val: number; // size
  description: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

export interface GraphLink {
  source: string;
  target: string;
  label?: string;
}

interface GraphViewProps {
  theme?: ThemeMode;
}

export const GraphView: React.FC<GraphViewProps> = ({ theme = 'dark' }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);

  // Zoom & Pan transformation state
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const isDraggingCanvas = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const draggedNode = useRef<GraphNode | null>(null);

  // Initial Semantic Graph Data (Agents, Memory, Skills, Active)
  const initialNodes: GraphNode[] = [
    // 🟠 Agents (Orange)
    { id: 'a1', label: 'MaxIM Core', type: 'agent', group: 'Executive', val: 14, description: 'Central autonomous orchestrator and ReAct decision engine.' },
    { id: 'a2', label: 'Code Architect', type: 'agent', group: 'Engineering', val: 9, description: 'Enforces system boundaries and anti-duplication rules (R01-R40).' },
    { id: 'a3', label: 'UI/UX Designer', type: 'agent', group: 'Design', val: 9, description: 'Refines modern monochrome aesthetics, micro-interactions, and visual harmony.' },
    { id: 'a4', label: 'Reality Checker', type: 'agent', group: 'QA', val: 8, description: 'Demands verifiable test receipts, build logs, and empirical evidence.' },
    { id: 'a5', label: 'Obsidian Agent', type: 'agent', group: 'Knowledge', val: 8, description: 'Indexes and links markdown vault notes into SQLite WAL persistence.' },

    // ⚪ Memory (White / Slate)
    { id: 'm1', label: 'TELOS Targets', type: 'memory', group: 'Layer 3', val: 11, description: 'Master LifeOS and Autonomous Computer-Use Agent roadmap.' },
    { id: 'm2', label: 'Black & White Aesthetic', type: 'memory', group: 'Layer 3', val: 9, description: 'Minimalist high-contrast monochrome design directives.' },
    { id: 'm3', label: '5-Layer Memory Spec', type: 'memory', group: 'Layer 5', val: 10, description: 'Zylos inside-out context safeguards with SQLite storage.' },
    { id: 'm4', label: 'Working Context', type: 'memory', group: 'Layer 1', val: 8, description: 'Active token budget and conversation context buffer.' },
    { id: 'm5', label: 'Vault Index (214 Notes)', type: 'memory', group: 'Layer 5', val: 10, description: 'Real-time filesystem watcher synchronization table.' },

    // 🔵 Skills / Tools (Blue)
    { id: 's1', label: 'FastMCP Registry', type: 'skill', group: 'Tools', val: 11, description: 'Multi-server protocol runner with lazy tool mounting.' },
    { id: 's2', label: 'Terminal Runner', type: 'skill', group: 'Tools', val: 8, description: 'Sandboxed PowerShell execution with token compression.' },
    { id: 's3', label: 'Computer Vision', type: 'skill', group: 'Tools', val: 9, description: 'Real-time webcam & screen capture frame analysis.' },
    { id: 's4', label: 'Web Search Gateway', type: 'skill', group: 'Tools', val: 8, description: 'Real-time web retrieval and source verification.' },
    { id: 's5', label: 'Audio Duplex Engine', type: 'skill', group: 'Tools', val: 8, description: 'Hands-free voice recognition and speech synthesis loop.' },

    // 🟢 Active Sessions / Tasks (Emerald)
    { id: 'act1', label: 'Active Home Cockpit', type: 'active', group: 'Session', val: 10, description: 'Real-time interactive dashboard cockpit session.' },
    { id: 'act2', label: 'Hardware Telemetry Sync', type: 'active', group: 'Session', val: 7, description: 'Continuous CPU, RAM, and GPU VRAM polling daemon.' },
    { id: 'act3', label: 'Vector Lip-Sync Rig', type: 'active', group: 'Session', val: 8, description: 'Dynamic Kai mascot articulation and state machine.' },
  ];

  const initialLinks: GraphLink[] = [
    { source: 'a1', target: 'm1' },
    { source: 'a1', target: 'a2' },
    { source: 'a1', target: 'a3' },
    { source: 'a1', target: 'a4' },
    { source: 'a1', target: 'a5' },
    { source: 'a1', target: 's1' },
    { source: 'a1', target: 'act1' },
    { source: 'a3', target: 'm2' },
    { source: 'a3', target: 'act3' },
    { source: 'a5', target: 'm3' },
    { source: 'a5', target: 'm5' },
    { source: 's1', target: 's2' },
    { source: 's1', target: 's3' },
    { source: 's1', target: 's4' },
    { source: 's1', target: 's5' },
    { source: 'act1', target: 'act2' },
    { source: 'act1', target: 'act3' },
    { source: 's3', target: 'act1' },
    { source: 'm4', target: 'act1' },
    { source: 'a4', target: 's2' },
  ];

  const [nodes] = useState<GraphNode[]>(() => {
    // Distribute nodes randomly in a gentle circle
    const count = initialNodes.length;
    return initialNodes.map((n, i) => {
      const angle = (i / count) * 2 * Math.PI;
      const radius = 140 + (i % 3) * 60;
      return {
        ...n,
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
      };
    });
  });

  const [links] = useState<GraphLink[]>(initialLinks);

  // Colors mapping strictly per specification
  const getNodeColor = (type: NodeType): string => {
    switch (type) {
      case 'agent':
        return '#f97316'; // 🟠 Orange: Agents
      case 'memory':
        return theme === 'light' ? '#09090b' : '#fafafa'; // ⚪ White/Onyx: Memory
      case 'skill':
        return '#3b82f6'; // 🔵 Blue: Skills & Tools
      case 'active':
        return '#10b981'; // 🟢 Emerald: Active sessions
    }
  };

  // 60FPS Physics Simulation & Render Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx || typeof ctx.save !== 'function') return;

    let animationFrameId: number;

    const render = () => {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }

      ctx.clearRect(0, 0, width, height);

      ctx.save();
      // Center canvas origin
      ctx.translate(width / 2 + pan.x, height / 2 + pan.y);
      ctx.scale(zoom, zoom);

      // Node lookup map
      const nodeMap = new Map<string, GraphNode>();
      nodes.forEach((n) => nodeMap.set(n.id, n));

      // Draw Edges / Links
      links.forEach((link) => {
        const source = nodeMap.get(link.source);
        const target = nodeMap.get(link.target);
        if (!source || !target || source.x == null || source.y == null || target.x == null || target.y == null) return;

        const isConnectedToHovered =
          hoveredNode && (hoveredNode.id === source.id || hoveredNode.id === target.id);

        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.strokeStyle = isConnectedToHovered
          ? (theme === 'light' ? 'rgba(0,0,0,0.6)' : 'rgba(255,255,255,0.7)')
          : (theme === 'light' ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.08)');
        ctx.lineWidth = isConnectedToHovered ? 1.5 : 1;
        ctx.stroke();
      });

      // Draw Nodes
      nodes.forEach((node) => {
        if (node.x == null || node.y == null) return;

        const isFiltered =
          (selectedType !== 'all' && node.type !== selectedType) ||
          (searchQuery && !node.label.toLowerCase().includes(searchQuery.toLowerCase()));

        const isSelected = selectedNode?.id === node.id;
        const isHovered = hoveredNode?.id === node.id;
        const color = getNodeColor(node.type);

        ctx.save();
        ctx.globalAlpha = isFiltered ? 0.15 : 1.0;

        // Outer Glow / Halo for Active or Selected Nodes
        if (isSelected || isHovered || node.type === 'active') {
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.val + (isHovered ? 6 : 4), 0, Math.PI * 2);
          ctx.fillStyle = node.type === 'active' ? 'rgba(16, 185, 129, 0.25)' : 'rgba(255,255,255,0.15)';
          ctx.fill();
        }

        // Main Node Circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.val, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();

        // Node Inner Border
        ctx.strokeStyle = theme === 'light' ? 'rgba(0,0,0,0.2)' : 'rgba(255,255,255,0.2)';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Text Label
        ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillStyle = isSelected
          ? (theme === 'light' ? '#000000' : '#ffffff')
          : (theme === 'light' ? '#475569' : '#a1a1aa');
        ctx.fillText(node.label, node.x, node.y + node.val + 4);

        ctx.restore();
      });

      ctx.restore();

      // Physics Relaxation Step (Organic Force Drift)
      nodes.forEach((n1, i) => {
        if (draggedNode.current?.id === n1.id) return;

        // Repulsion between nodes
        for (let j = i + 1; j < nodes.length; j++) {
          const n2 = nodes[j];
          if (n1.x == null || n1.y == null || n2.x == null || n2.y == null) continue;
          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          if (dist < 180) {
            const force = (180 - dist) / 180;
            const fx = (dx / dist) * force * 0.4;
            const fy = (dy / dist) * force * 0.4;
            n1.vx = (n1.vx || 0) - fx;
            n1.vy = (n1.vy || 0) - fy;
            n2.vx = (n2.vx || 0) + fx;
            n2.vy = (n2.vy || 0) + fy;
          }
        }

        // Center gravitation
        if (n1.x != null && n1.y != null) {
          n1.vx = (n1.vx || 0) - n1.x * 0.001;
          n1.vy = (n1.vy || 0) - n1.y * 0.001;

          // Apply velocity with damping
          n1.x += n1.vx || 0;
          n1.y += n1.vy || 0;
          n1.vx = (n1.vx || 0) * 0.88;
          n1.vy = (n1.vy || 0) * 0.88;
        }
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [nodes, links, zoom, pan, hoveredNode, selectedNode, selectedType, searchQuery, theme]);

  // Transform Screen Mouse Coordinates to Canvas Coordinates
  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    return {
      x: (mouseX - canvas.width / 2 - pan.x) / zoom,
      y: (mouseY - canvas.height / 2 - pan.y) / zoom,
    };
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const coords = getCanvasCoords(e);
    // Check if clicked a node
    const clicked = nodes.find((n) => {
      if (n.x == null || n.y == null) return false;
      const dx = n.x - coords.x;
      const dy = n.y - coords.y;
      return Math.sqrt(dx * dx + dy * dy) <= n.val + 5;
    });

    if (clicked) {
      draggedNode.current = clicked;
      setSelectedNode(clicked);
    } else {
      isDraggingCanvas.current = true;
      dragStart.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (draggedNode.current) {
      const coords = getCanvasCoords(e);
      draggedNode.current.x = coords.x;
      draggedNode.current.y = coords.y;
      draggedNode.current.vx = 0;
      draggedNode.current.vy = 0;
    } else if (isDraggingCanvas.current) {
      setPan({
        x: e.clientX - dragStart.current.x,
        y: e.clientY - dragStart.current.y,
      });
    } else {
      const coords = getCanvasCoords(e);
      const hovered = nodes.find((n) => {
        if (n.x == null || n.y == null) return false;
        const dx = n.x - coords.x;
        const dy = n.y - coords.y;
        return Math.sqrt(dx * dx + dy * dy) <= n.val + 5;
      });
      setHoveredNode(hovered || null);
    }
  };

  const handleMouseUp = () => {
    draggedNode.current = null;
    isDraggingCanvas.current = false;
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    setZoom((prev) => Math.min(3, Math.max(0.4, prev * zoomFactor)));
  };

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setSelectedNode(null);
  };

  // Connected nodes for the inspector
  const connectedNodes = selectedNode
    ? links
        .filter((l) => l.source === selectedNode.id || l.target === selectedNode.id)
        .map((l) => (l.source === selectedNode.id ? l.target : l.source))
        .map((id) => nodes.find((n) => n.id === id))
        .filter(Boolean) as GraphNode[]
    : [];

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden select-none font-sans relative">
      {/* 1. Header & Topology Controls */}
      <div className="h-14 border-b border-border-subtle px-6 flex items-center justify-between bg-bg-card/70 backdrop-blur-md z-10 flex-shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <Network className="w-4 h-4 text-text-secondary" />
            <h1 className="text-sm font-semibold tracking-tight text-text-primary">
              Interactive Force-Directed Knowledge Graph
            </h1>
          </div>
          <p className="text-[11px] text-text-muted">
            Obsidian-style topological view connecting agents, memory, tools, and active sessions.
          </p>
        </div>

        {/* Color-Coded Semantic Legend (Strict Spec) */}
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500 shadow-sm" />
            <span className="text-text-secondary">Agents</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500 shadow-sm" />
            <span className="text-text-secondary">Skills</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-900 dark:bg-white shadow-sm" />
            <span className="text-text-secondary">Memory</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse shadow-sm" />
            <span className="text-text-secondary">Active Session</span>
          </div>
        </div>
      </div>

      {/* 2. Interactive Canvas Stage */}
      <div className="flex-1 relative overflow-hidden bg-bg-main">
        {/* Floating Top Filter Dock */}
        <div className="absolute top-4 left-4 z-10 flex items-center gap-2">
          {/* Search Input */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-border-subtle bg-bg-card/90 backdrop-blur-md shadow-md text-xs">
            <Search className="w-3.5 h-3.5 text-text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search graph nodes..."
              className="bg-transparent text-xs text-text-primary placeholder:text-text-muted outline-none w-40 font-sans"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="text-text-muted hover:text-text-primary">
                <X className="w-3 h-3" />
              </button>
            )}
          </div>

          {/* Type Filter Pills */}
          <div className="flex items-center gap-1 p-1 rounded-xl border border-border-subtle bg-bg-card/90 backdrop-blur-md shadow-md text-[11px] font-mono">
            {['all', 'agent', 'memory', 'skill', 'active'].map((t) => (
              <button
                key={t}
                onClick={() => setSelectedType(t)}
                className={`px-2 py-0.5 rounded-lg capitalize transition-all ${
                  selectedType === t
                    ? 'bg-accent text-accent-contrast font-semibold shadow-xs'
                    : 'text-text-muted hover:text-text-primary hover:bg-bg-card-hover'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* Floating Viewport Controls */}
        <div className="absolute bottom-4 left-4 z-10 flex items-center gap-1.5 p-1 rounded-xl border border-border-subtle bg-bg-card/90 backdrop-blur-md shadow-md">
          <button
            onClick={() => setZoom((z) => Math.min(3, z * 1.2))}
            className="p-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-card-hover transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setZoom((z) => Math.max(0.4, z * 0.8))}
            className="p-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-card-hover transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={resetView}
            className="p-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-card-hover transition-colors"
            title="Reset View"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>

        {/* Node & Link Count HUD */}
        <div className="absolute bottom-4 right-4 z-10 px-3 py-1.5 rounded-xl border border-border-subtle bg-bg-card/90 backdrop-blur-md shadow-md font-mono text-[11px] text-text-muted flex items-center gap-2">
          <span>{nodes.length} Nodes</span>
          <span className="text-border-subtle">•</span>
          <span>{links.length} Edges</span>
        </div>

        {/* The Simulation Canvas */}
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
          className="w-full h-full cursor-grab active:cursor-grabbing block"
        />

        {/* Node Inspector Drawer */}
        {selectedNode && (
          <div className="absolute top-4 right-4 z-20 w-80 rounded-2xl border border-border-subtle bg-bg-card p-5 shadow-2xl flex flex-col gap-3 animate-in fade-in slide-in-from-right-4 duration-150 backdrop-blur-xl">
            <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
              <div className="flex items-center gap-2">
                <span
                  className="w-3 h-3 rounded-full shadow-sm"
                  style={{ backgroundColor: getNodeColor(selectedNode.type) }}
                />
                <span className="text-xs font-mono uppercase font-semibold text-text-secondary">
                  {selectedNode.type} Node
                </span>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="p-1 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-card-hover"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div>
              <h3 className="text-base font-bold text-text-primary">{selectedNode.label}</h3>
              <span className="text-[11px] font-mono text-text-muted">
                Group: {selectedNode.group}
              </span>
            </div>

            <p className="text-xs text-text-secondary leading-relaxed font-sans">
              {selectedNode.description}
            </p>

            {/* Connected Nodes List */}
            <div className="pt-2 border-t border-border-subtle flex flex-col gap-1.5">
              <span className="text-[11px] font-mono text-text-muted uppercase tracking-wider">
                Connected Nodes ({connectedNodes.length})
              </span>
              <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto">
                {connectedNodes.map((cn) => (
                  <button
                    key={cn.id}
                    onClick={() => setSelectedNode(cn)}
                    className="flex items-center gap-1.5 px-2 py-1 rounded-lg border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover text-[11px] font-mono text-text-primary transition-colors"
                  >
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: getNodeColor(cn.type) }}
                    />
                    <span>{cn.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
