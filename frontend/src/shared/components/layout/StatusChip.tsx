import type { ReactNode } from 'react';

import { cn } from '../../utils/cn';

type StatusTone = 'default' | 'success' | 'warning' | 'error' | 'info';

const toneClassMap: Record<StatusTone, string> = {
  default: 'border-[color:var(--color-app-border)] bg-[color:var(--color-app-surface-raised)] text-[color:var(--color-text-secondary)]',
  success: 'border-[color:var(--color-success)]/40 bg-[color:var(--color-success)]/15 text-[color:var(--color-success)]',
  warning: 'border-[color:var(--color-warning)]/40 bg-[color:var(--color-warning)]/15 text-[color:var(--color-warning)]',
  error: 'border-[color:var(--color-error)]/40 bg-[color:var(--color-error)]/15 text-[color:var(--color-error)]',
  info: 'border-[color:var(--color-primary)]/40 bg-[color:var(--color-primary)]/15 text-[color:var(--color-primary)]',
};

interface StatusChipProps {
  children: ReactNode;
  tone?: StatusTone;
  className?: string;
}

export function StatusChip({ children, tone = 'default', className }: StatusChipProps) {
  return (
    <span
      data-testid="status-chip"
      className={cn(
        'inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide',
        toneClassMap[tone],
        className
      )}
    >
      {children}
    </span>
  );
}
