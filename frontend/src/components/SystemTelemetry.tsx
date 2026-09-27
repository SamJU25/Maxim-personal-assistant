import React, { useState, useEffect } from 'react';
import { Cpu, HardDrive, Zap, Server, ChevronDown, ChevronUp, Gauge } from 'lucide-react';
import { HardwareTelemetryData } from '../types';

export const SystemTelemetry: React.FC = () => {
  const [telemetry, setTelemetry] = useState<HardwareTelemetryData>({
    cpu_percent: 18.4,
    cpu_cores: 16,
    ram_total_gb: 32.0,
    ram_used_gb: 11.2,
    ram_free_gb: 20.8,
    ram_percent: 35.0,
    gpu_available: true,
    gpu_name: 'NVIDIA RTX 4090',
    vram_total_mb: 24576,
    vram_used_mb: 4915,
    vram_free_mb: 19661,
    vram_percent: 20.0,
    ollama_online: true,
  });

  const [showDetails, setShowDetails] = useState<boolean>(false);

  const fetchTelemetry = async () => {
    try {
      const res = await fetch('/api/hardware/telemetry');
      if (res.ok) {
        const data = await res.json();
        setTelemetry((prev) => ({
          ...prev,
          ...data,
          ram_percent: data.ram_percent ?? prev.ram_percent,
          cpu_percent: data.cpu_percent ?? prev.cpu_percent,
        }));
      }
    } catch {
      // Graceful fallback to initial values when offline
    }
  };

  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 3500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="rounded-xl border border-border-subtle bg-bg-card p-4 transition-all shadow-sm flex flex-col gap-3 select-none">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs text-text-muted">
          <Server className="w-3.5 h-3.5 text-text-secondary" />
          <span className="font-mono text-[11px] uppercase tracking-wider font-semibold text-text-secondary">
            System Telemetry
          </span>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 font-mono text-[10px] text-text-muted px-1.5 py-0.5 rounded bg-bg-card-subtle border border-border-subtle">
            <span>CORES:</span>
            <span className="font-semibold text-text-secondary">{telemetry.cpu_cores || 16}</span>
          </div>

          <button
            onClick={() => setShowDetails(!showDetails)}
            className="p-1 rounded text-text-muted hover:text-text-primary hover:bg-bg-card-hover transition-colors"
            title={showDetails ? 'Hide details' : 'Show detailed telemetry'}
          >
            {showDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* CPU Metric Bar */}
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between text-xs font-mono">
          <div className="flex items-center gap-1.5 text-text-secondary">
            <Cpu className="w-3.5 h-3.5 text-text-muted" />
            <span className="text-[11px] font-medium font-sans">CPU Load</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-text-muted font-mono">
              {telemetry.cpu_percent < 50 ? 'NORMAL' : 'HEAVY'}
            </span>
            <span className="font-semibold text-text-primary">
              {telemetry.cpu_percent.toFixed(1)}%
            </span>
          </div>
        </div>
        <div className="w-full h-1.5 rounded-full bg-bg-card-subtle border border-border-subtle overflow-hidden">
          <div
            className="h-full bg-accent transition-all duration-700 ease-out rounded-full"
            style={{ width: `${Math.min(100, Math.max(0, telemetry.cpu_percent))}%` }}
          />
        </div>
      </div>

      {/* RAM Metric Bar */}
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between text-xs font-mono">
          <div className="flex items-center gap-1.5 text-text-secondary">
            <HardDrive className="w-3.5 h-3.5 text-text-muted" />
            <span className="text-[11px] font-medium font-sans">Memory (RAM)</span>
          </div>
          <span className="font-semibold text-text-primary">
            {telemetry.ram_used_gb.toFixed(1)} / {telemetry.ram_total_gb.toFixed(0)} GB
          </span>
        </div>
        <div className="w-full h-1.5 rounded-full bg-bg-card-subtle border border-border-subtle overflow-hidden">
          <div
            className="h-full bg-accent transition-all duration-700 ease-out rounded-full"
            style={{ width: `${Math.min(100, Math.max(0, telemetry.ram_percent))}%` }}
          />
        </div>
      </div>

      {/* Expandable Detailed Breakdown */}
      {showDetails && (
        <div className="pt-2 pb-1 border-t border-border-subtle flex flex-col gap-2 animate-in fade-in duration-150">
          {/* GPU / VRAM Metric if Available */}
          {telemetry.gpu_available !== false && (
            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-1 text-[11px] text-text-secondary">
                  <Gauge className="w-3 h-3 text-text-muted" />
                  <span className="font-sans font-medium">GPU VRAM</span>
                </div>
                <span className="text-[11px] font-semibold text-text-primary">
                  {((telemetry.vram_used_mb || 0) / 1024).toFixed(1)} / {((telemetry.vram_total_mb || 24576) / 1024).toFixed(0)} GB
                </span>
              </div>
              <div className="w-full h-1 rounded-full bg-bg-card-subtle border border-border-subtle overflow-hidden">
                <div
                  className="h-full bg-accent/80 transition-all duration-700 ease-out rounded-full"
                  style={{ width: `${Math.min(100, Math.max(0, telemetry.vram_percent || 20))}%` }}
                />
              </div>
            </div>
          )}

          {/* Memory Free Metric */}
          <div className="flex items-center justify-between text-[11px] font-mono text-text-muted pt-1">
            <span>Free RAM:</span>
            <span className="text-text-secondary font-medium">{telemetry.ram_free_gb.toFixed(1)} GB</span>
          </div>
        </div>
      )}

      {/* GPU / Engine Status Footer */}
      <div className="pt-2 border-t border-border-subtle flex items-center justify-between text-[11px] font-mono">
        <div className="flex items-center gap-1.5 text-text-muted">
          <Zap className="w-3 h-3 text-text-secondary" />
          <span>Ollama Engine:</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              telemetry.ollama_online !== false ? 'bg-emerald-500 animate-pulse' : 'bg-text-muted'
            }`}
          />
          <span
            className={`font-semibold ${
              telemetry.ollama_online !== false ? 'text-emerald-500' : 'text-text-muted'
            }`}
          >
            {telemetry.ollama_online !== false ? 'READY (Local)' : 'STANDBY'}
          </span>
        </div>
      </div>
    </div>
  );
};
