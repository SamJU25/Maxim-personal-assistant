import React, { useState, useEffect } from 'react';
import {
  Database,
  Plus,
  Search,
  Layers,
  Brain,
  FileText,
  Clock,
  CheckCircle2,
  X,
  Tag,
} from 'lucide-react';

interface MemoryItem {
  id: string;
  content: string;
  category: 'semantic' | 'episodic' | 'procedural' | 'vault' | 'preference';
  source: string;
  confidence: number;
  timestamp: string;
}

export const MemoryView: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // New Memory Form State
  const [newContent, setNewContent] = useState('');
  const [newCategory, setNewCategory] = useState<'semantic' | 'preference' | 'procedural' | 'vault'>('semantic');
  const [newSource, setNewSource] = useState('manual_user_entry');

  const [memories, setMemories] = useState<MemoryItem[]>([
    {
      id: 'mem-1',
      content: 'User prefers minimal, modern, high-contrast Black & White aesthetic without neon AI glow.',
      category: 'preference',
      source: 'user_directive',
      confidence: 1.0,
      timestamp: 'Today, 16:02',
    },
    {
      id: 'mem-2',
      content: 'TELOS Target: Master LifeOS & Autonomous Computer-Use Agent with SQLite WAL persistence.',
      category: 'semantic',
      source: 'obsidian_vault/TELOS.md',
      confidence: 0.98,
      timestamp: 'Yesterday',
    },
    {
      id: 'mem-3',
      content: 'FastMCP Registry Hub provides dynamic Smithery and Glama tool discovery without catalog bloat.',
      category: 'procedural',
      source: 'backend/tools/mcp_client.py',
      confidence: 0.95,
      timestamp: 'Sep 24, 2026',
    },
    {
      id: 'mem-4',
      content: 'Audio duplex loop uses Web Speech API and streaming TTS for hands-free voice interaction.',
      category: 'episodic',
      source: 'agent_reflection',
      confidence: 0.91,
      timestamp: 'Sep 23, 2026',
    },
    {
      id: 'mem-5',
      content: 'Obsidian markdown files indexed: 214 notes, 48 episodic traces, 1420 working context tokens.',
      category: 'vault',
      source: 'obsidian_vault_indexer',
      confidence: 1.0,
      timestamp: 'Sep 22, 2026',
    },
  ]);

  const fetchBackendMemories = async () => {
    try {
      const res = await fetch('/api/memory/five-layers');
      if (res.ok) {
        const data = await res.json();
        if (data.memories && Array.isArray(data.memories)) {
          setMemories(data.memories);
        }
      }
    } catch {
      // Graceful fallback to initial state when offline
    }
  };

  useEffect(() => {
    fetchBackendMemories();
  }, []);

  const handleAddMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newContent.trim()) return;

    const newItem: MemoryItem = {
      id: `mem-${Date.now()}`,
      content: newContent.trim(),
      category: newCategory,
      source: newSource.trim() || 'manual_user_entry',
      confidence: 1.0,
      timestamp: 'Just now',
    };

    // Optimistic update
    setMemories((prev) => [newItem, ...prev]);

    // Send to backend endpoint if available
    try {
      await fetch('/api/memory/retain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: newItem.content,
          category: newItem.category,
          source: newItem.source,
          confidence: newItem.confidence,
        }),
      });
    } catch {
      // Offline fallback
    }

    setNewContent('');
    setIsAddModalOpen(false);
  };

  const filteredMemories = memories.filter((m) => {
    const matchesSearch =
      m.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.source.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCat = selectedCategory === 'all' || m.category === selectedCategory;
    return matchesSearch && matchesCat;
  });

  return (
    <div className="flex-1 p-8 flex flex-col gap-6 overflow-y-auto select-none font-sans">
      {/* 1. Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle pb-5">
        <div>
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-text-secondary" />
            <h1 className="text-xl font-bold tracking-tight text-text-primary">
              Obsidian Knowledge & Memory Store
            </h1>
          </div>
          <p className="text-xs text-text-muted mt-1">
            Zylos 5-Layer inside-out semantic memory, episodic traces, and contextual knowledge graphs.
          </p>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-accent text-accent-contrast text-xs font-semibold shadow-sm hover:opacity-90 transition-all active:scale-95"
        >
          <Plus className="w-4 h-4" />
          <span>Add Memory Manually</span>
        </button>
      </div>

      {/* 2. The 5-Layer Architecture Visual Grid */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3.5">
        {/* Layer 1 */}
        <div className="p-3.5 rounded-xl border border-border-subtle bg-bg-card flex flex-col justify-between shadow-xs">
          <div>
            <div className="flex items-center justify-between text-[11px] font-mono text-text-muted mb-1">
              <span>LAYER 1</span>
              <Brain className="w-3 h-3 text-text-secondary" />
            </div>
            <h3 className="text-xs font-semibold text-text-primary">Working Context</h3>
            <p className="text-[11px] text-text-muted mt-0.5">Active conversation tokens</p>
          </div>
          <div className="mt-3 text-base font-mono font-bold text-text-primary">1,420 tokens</div>
        </div>

        {/* Layer 2 */}
        <div className="p-3.5 rounded-xl border border-border-subtle bg-bg-card flex flex-col justify-between shadow-xs">
          <div>
            <div className="flex items-center justify-between text-[11px] font-mono text-text-muted mb-1">
              <span>LAYER 2</span>
              <Clock className="w-3 h-3 text-text-secondary" />
            </div>
            <h3 className="text-xs font-semibold text-text-primary">Episodic Traces</h3>
            <p className="text-[11px] text-text-muted mt-0.5">Recent task outcomes</p>
          </div>
          <div className="mt-3 text-base font-mono font-bold text-text-primary">48 records</div>
        </div>

        {/* Layer 3 */}
        <div className="p-3.5 rounded-xl border border-border-subtle bg-bg-card flex flex-col justify-between shadow-xs">
          <div>
            <div className="flex items-center justify-between text-[11px] font-mono text-text-muted mb-1">
              <span>LAYER 3</span>
              <Tag className="w-3 h-3 text-text-secondary" />
            </div>
            <h3 className="text-xs font-semibold text-text-primary">Semantic Knowledge</h3>
            <p className="text-[11px] text-text-muted mt-0.5">Long-term facts & entities</p>
          </div>
          <div className="mt-3 text-base font-mono font-bold text-text-primary">156 facts</div>
        </div>

        {/* Layer 4 */}
        <div className="p-3.5 rounded-xl border border-border-subtle bg-bg-card flex flex-col justify-between shadow-xs">
          <div>
            <div className="flex items-center justify-between text-[11px] font-mono text-text-muted mb-1">
              <span>LAYER 4</span>
              <Layers className="w-3 h-3 text-text-secondary" />
            </div>
            <h3 className="text-xs font-semibold text-text-primary">Procedural Skills</h3>
            <p className="text-[11px] text-text-muted mt-0.5">Proven tool patterns</p>
          </div>
          <div className="mt-3 text-base font-mono font-bold text-text-primary">18 tools</div>
        </div>

        {/* Layer 5 */}
        <div className="p-3.5 rounded-xl border border-border-subtle bg-bg-card flex flex-col justify-between shadow-xs">
          <div>
            <div className="flex items-center justify-between text-[11px] font-mono text-text-muted mb-1">
              <span>LAYER 5</span>
              <FileText className="w-3 h-3 text-text-secondary" />
            </div>
            <h3 className="text-xs font-semibold text-text-primary">Obsidian Vault</h3>
            <p className="text-[11px] text-text-muted mt-0.5">WAL SQLite indexed notes</p>
          </div>
          <div className="mt-3 text-base font-mono font-bold text-text-primary">214 notes</div>
        </div>
      </div>

      {/* 3. Search and Category Filter Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-bg-card p-2.5 rounded-xl border border-border-subtle">
        {/* Search Input */}
        <div className="flex-1 flex items-center gap-2 bg-bg-card-subtle px-3 py-1.5 rounded-lg border border-border-subtle focus-within:border-border-active transition-colors">
          <Search className="w-3.5 h-3.5 text-text-muted" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search memory facts, entities, or vault provenance..."
            className="flex-1 bg-transparent text-xs text-text-primary placeholder:text-text-muted outline-none font-sans"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery('')} className="text-text-muted hover:text-text-primary">
              <X className="w-3 h-3" />
            </button>
          )}
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-1 overflow-x-auto pb-0.5">
          {['all', 'preference', 'semantic', 'procedural', 'episodic', 'vault'].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-mono uppercase tracking-wider transition-all ${
                selectedCategory === cat
                  ? 'bg-accent text-accent-contrast font-semibold shadow-xs'
                  : 'text-text-secondary hover:text-text-primary hover:bg-bg-card-hover'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* 4. Retained Facts & Knowledge List */}
      <div className="flex flex-col gap-2.5">
        <div className="flex items-center justify-between text-xs font-mono text-text-muted px-1">
          <span>MEMORIES ({filteredMemories.length})</span>
          <span>CONFIDENCE & PROVENANCE</span>
        </div>

        {filteredMemories.length === 0 ? (
          <div className="p-8 rounded-xl border border-border-subtle bg-bg-card text-center flex flex-col items-center justify-center gap-2">
            <Search className="w-8 h-8 text-text-muted" />
            <p className="text-xs font-medium text-text-secondary">No matching memories found</p>
            <p className="text-[11px] text-text-muted font-mono">Try adjusting your search query or category filter.</p>
          </div>
        ) : (
          filteredMemories.map((mem) => (
            <div
              key={mem.id}
              className="p-4 rounded-xl border border-border-subtle bg-bg-card hover:border-border-active transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs group"
            >
              {/* Content & Category */}
              <div className="flex-1 flex flex-col gap-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded border border-border-subtle bg-bg-card-subtle text-text-secondary font-semibold">
                    {mem.category}
                  </span>
                  <span className="text-[11px] text-text-muted font-mono">
                    {mem.timestamp}
                  </span>
                </div>
                <p className="text-xs text-text-primary font-medium leading-relaxed font-sans">
                  {mem.content}
                </p>
              </div>

              {/* Provenance & Confidence Badge */}
              <div className="flex items-center gap-3 sm:text-right font-mono text-[11px] flex-shrink-0">
                <div className="flex flex-col sm:items-end">
                  <span className="text-text-secondary text-[11px] truncate max-w-[160px]">
                    {mem.source}
                  </span>
                  <div className="flex items-center gap-1 text-[10px] text-text-muted">
                    <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                    <span>{Math.round(mem.confidence * 100)}% Match</span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* 5. Add Memory Modal Dialog */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-150">
          <div className="w-full max-w-lg rounded-2xl border border-border-subtle bg-bg-card p-6 shadow-2xl flex flex-col gap-4">
            <div className="flex items-center justify-between pb-3 border-b border-border-subtle">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-text-primary" />
                <h3 className="text-sm font-semibold text-text-primary">Add Memory Manually</h3>
              </div>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-card-hover"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddMemory} className="flex flex-col gap-4">
              {/* Memory Content Textarea */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-text-secondary font-mono">
                  MEMORY CONTENT / FACT
                </label>
                <textarea
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  placeholder="e.g. MaxIM V2 uses local SQLite WAL mode for zero data loss and persistent session memory..."
                  rows={4}
                  required
                  className="w-full p-3 rounded-xl bg-bg-card-subtle border border-border-subtle text-xs text-text-primary placeholder:text-text-muted outline-none focus:border-border-active resize-none font-sans"
                />
              </div>

              {/* Category & Provenance Row */}
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-text-secondary font-mono">
                    LAYER CATEGORY
                  </label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value as any)}
                    className="p-2.5 rounded-xl bg-bg-card-subtle border border-border-subtle text-xs text-text-primary outline-none cursor-pointer"
                  >
                    <option value="semantic">Semantic Fact (Layer 3)</option>
                    <option value="preference">User Preference</option>
                    <option value="procedural">Procedural Pattern (Layer 4)</option>
                    <option value="vault">Vault Document Note (Layer 5)</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-text-secondary font-mono">
                    PROVENANCE / SOURCE
                  </label>
                  <input
                    type="text"
                    value={newSource}
                    onChange={(e) => setNewSource(e.target.value)}
                    placeholder="manual_user_entry"
                    className="p-2.5 rounded-xl bg-bg-card-subtle border border-border-subtle text-xs text-text-primary outline-none"
                  />
                </div>
              </div>

              {/* Form Action Buttons */}
              <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-border-subtle">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-medium text-text-muted hover:text-text-primary transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!newContent.trim()}
                  className={`px-5 py-2 rounded-xl text-xs font-semibold transition-all ${
                    newContent.trim()
                      ? 'bg-accent text-accent-contrast shadow-sm hover:opacity-90 active:scale-95'
                      : 'opacity-40 cursor-not-allowed bg-accent text-accent-contrast'
                  }`}
                >
                  Save to Memory Store
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
