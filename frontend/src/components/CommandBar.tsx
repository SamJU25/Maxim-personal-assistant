import React, { FormEvent, useRef, useEffect } from 'react';
import { Mic, Square, Camera, ArrowUp } from 'lucide-react';

export interface CommandBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (text: string) => void;
  onVoiceToggle?: () => void;
  onOpenUplinkModal?: () => void;
  onCancel?: () => void;
  isListening?: boolean;
  isSpeaking?: boolean;
  isRunning?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export const CommandBar: React.FC<CommandBarProps> = ({
  value,
  onChange,
  onSubmit,
  onVoiceToggle,
  onOpenUplinkModal,
  onCancel,
  isListening = false,
  isSpeaking = false,
  isRunning = false,
  disabled = false,
  placeholder,
}) => {
  const inputRef = useRef<HTMLInputElement | null>(null);

  // Auto-focus input when not listening
  useEffect(() => {
    if (!isListening && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isListening]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!value.trim() || isRunning) return;
    onSubmit(value.trim());
  };

  const isInterruptible = isRunning || isSpeaking;

  const dynamicPlaceholder = placeholder || (
    isListening
      ? 'Listening... Speak your command or question'
      : isSpeaking
      ? 'Kai is speaking... Press mic or stop to interrupt'
      : isRunning
      ? 'Reasoning through directive...'
      : 'Ask Kai anything, capture a thought, or hold mic to speak...'
  );

  return (
    <div className="w-full max-w-3xl mx-auto px-4 select-none">
      <form
        onSubmit={handleSubmit}
        className={`glass-panel rounded-2xl p-1.5 sm:p-2 flex items-center gap-2 sm:gap-3 shadow-2xl transition-all duration-200 border ${
          isListening
            ? 'border-accent shadow-[0_0_24px_var(--accent-glow)]'
            : 'border-border-subtle focus-within:border-accent/70 focus-within:shadow-[0_0_18px_var(--accent-glow)]'
        }`}
      >
        {/* Voice Microphone Toggle Button */}
        <button
          type="button"
          onClick={onVoiceToggle}
          disabled={disabled}
          className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all cursor-pointer btn-press shrink-0 ${
            isListening
              ? 'bg-accent text-accent-contrast animate-acoustic-pulse shadow-md'
              : 'bg-bg-card-subtle text-text-secondary hover:text-text-primary hover:bg-bg-card-hover border border-border-subtle'
          }`}
          title={isListening ? 'Stop Listening' : 'Start Voice Conversation'}
          aria-label={isListening ? 'Stop Listening' : 'Start Voice Conversation'}
          aria-pressed={isListening}
        >
          {isListening ? (
            <Mic className="w-4 h-4 fill-current animate-pulse" />
          ) : (
            <Mic className="w-4 h-4" />
          )}
        </button>

        {/* Text Input Surface */}
        <div className="flex-1 flex items-center min-w-0">
          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled || isRunning}
            placeholder={dynamicPlaceholder}
            className="w-full bg-transparent border-none outline-none text-sm text-text-primary placeholder:text-text-muted px-2 py-1.5 caret-accent font-sans"
            autoComplete="off"
            spellCheck="false"
          />
        </div>

        {/* Vision / Screen Perception Uplink Button */}
        {onOpenUplinkModal && (
          <button
            type="button"
            onClick={onOpenUplinkModal}
            disabled={disabled}
            className="w-9 h-9 rounded-xl flex items-center justify-center transition-all cursor-pointer btn-press shrink-0 bg-bg-card-subtle text-text-secondary hover:text-text-primary hover:bg-bg-card-hover border border-border-subtle"
            title="Open Visual Perception Uplink (Camera / Screen)"
            aria-label="Open Visual Perception Uplink"
          >
            <Camera className="w-4 h-4" />
          </button>
        )}

        {/* Keyboard Shortcut Indicator */}
        <kbd className="hidden sm:inline-flex items-center justify-center text-[10px] font-mono text-text-muted px-1.5 py-0.5 rounded border border-border-subtle bg-bg-card-subtle select-none">
          ↵ Enter
        </kbd>

        {/* Action Button: Send or Stop */}
        {isInterruptible ? (
          <button
            type="button"
            onClick={onCancel}
            className="w-10 h-10 rounded-xl flex items-center justify-center transition-all cursor-pointer btn-press shrink-0 bg-rose-500/20 text-rose-400 hover:bg-rose-500/30 border border-rose-500/40 shadow-sm"
            title={isRunning ? 'Cancel Reasoning' : 'Interrupt Speech'}
            aria-label="Stop Action"
          >
            <Square className="w-3.5 h-3.5 fill-current" />
          </button>
        ) : (
          <button
            type="submit"
            disabled={disabled || !value.trim() || isRunning}
            className="w-10 h-10 rounded-xl flex items-center justify-center transition-all cursor-pointer btn-press shrink-0 bg-accent text-accent-contrast disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 shadow-sm"
            title="Send Directive"
            aria-label="Send Directive"
          >
            <ArrowUp className="w-4 h-4 stroke-[2.5]" />
          </button>
        )}
      </form>
    </div>
  );
};
