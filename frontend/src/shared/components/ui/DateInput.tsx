import { useEffect, useRef, useState } from 'react';
import { DayPicker, type DayButtonProps } from 'react-day-picker';

import { cn } from '../../utils/cn';

export interface DateInputProps {
  label?: string;
  value?: string;
  onChange: (value: string) => void;
  onBlur?: () => void;
  error?: string;
  disabled?: boolean;
  id?: string;
}

function parseYMD(ymd: string): Date | undefined {
  if (!ymd) return undefined;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(ymd)) return undefined;
  const [y, m, d] = ymd.split('-').map(Number);
  if (!y || !m || !d || m > 12 || d > 31) return undefined;
  const date = new Date(y, m - 1, d);
  // Verifica que não houve overflow do Date (ex: 13/45 -> próximo mês)
  if (date.getMonth() !== m - 1 || date.getDate() !== d) return undefined;
  return date;
}

function toYMD(date: Date): string {
  const y = String(date.getFullYear());
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function formatDisplay(ymd?: string): string {
  if (!ymd) return 'DD/MM/AAAA';
  const date = parseYMD(ymd);
  if (!date) return 'DD/MM/AAAA';
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date);
}

const formatCaption = (month: Date) =>
  new Intl.DateTimeFormat('pt-BR', { month: 'long', year: 'numeric' }).format(month);

const formatWeekdayName = (day: Date) =>
  new Intl.DateTimeFormat('pt-BR', { weekday: 'short' }).format(day).replace('.', '');

function CustomDayButton({ day: _day, modifiers: _modifiers, ...buttonProps }: DayButtonProps) {
  return <button {...buttonProps} />;
}

export function DateInput({
  label,
  value,
  onChange,
  onBlur,
  error,
  disabled = false,
  id,
}: DateInputProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const selected = value ? parseYMD(value) : undefined;

  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
        onBlur?.();
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => {
      document.removeEventListener('mousedown', handleClick);
    };
  }, [open, onBlur]);

  const handleSelect = (date: Date | undefined) => {
    if (date) {
      onChange(toYMD(date));
      setOpen(false);
      onBlur?.();
    }
  };

  const ariaLabel = label
    ? `${label}: ${formatDisplay(value)}`
    : formatDisplay(value);

  return (
    <div className="w-full space-y-1.5" ref={containerRef}>
      {label && (
        <label
          htmlFor={id}
          className="text-sm font-medium text-text-secondary px-1"
        >
          {label}
        </label>
      )}
      <div className="relative">
        <button
          id={id}
          type="button"
          disabled={disabled}
          aria-expanded={open}
          aria-haspopup="dialog"
          aria-label={ariaLabel}
          onClick={() => {
            setOpen(prev => !prev);
          }}
          className={cn(
            'flex h-11 w-full items-center rounded-lg bg-dark-card border px-3 py-2 text-sm transition-all',
            'focus:outline-none focus:ring-2 focus:ring-gradient-start/20 focus:border-gradient-start',
            'disabled:cursor-not-allowed disabled:opacity-50',
            value ? 'text-text-primary' : 'text-text-muted',
            error
              ? 'border-red-500 focus:ring-red-500/20 focus:border-red-500'
              : 'border-border',
          )}
        >
          {formatDisplay(value)}
        </button>
        {open && (
          <div className="absolute z-50 mt-1 rounded-xl border border-border bg-dark-card shadow-lg p-3">
            <DayPicker
              mode="single"
              selected={selected}
              onSelect={handleSelect}
              defaultMonth={selected ?? new Date()}
              weekStartsOn={0}
              components={{ DayButton: CustomDayButton }}
              formatters={{
                formatCaption,
                formatWeekdayName,
              }}
            />
          </div>
        )}
      </div>
      {error && (
        <p className="text-xs font-medium text-red-500 px-1">{error}</p>
      )}
    </div>
  );
}
