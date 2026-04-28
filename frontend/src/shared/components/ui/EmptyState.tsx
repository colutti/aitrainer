import type { LucideIcon } from 'lucide-react';

import { cn } from '../../utils/cn';

import { Button } from './Button';

interface EmptyStateProps {
  title: string;
  description: string;
  icon: LucideIcon;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  title,
  description,
  icon: Icon,
  actionLabel,
  onAction,
  className
}: EmptyStateProps) {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center p-8 text-center bg-[color:var(--color-surface-container-low)] border border-[color:var(--color-outline-variant)] rounded-xl space-y-4",
      className
    )}>
      <div className="w-16 h-16 rounded-xl bg-[color:var(--color-surface-container)] flex items-center justify-center text-[color:var(--color-on-surface-variant)] mb-2">
        <Icon size={32} />
      </div>
      
      <div className="space-y-2 max-w-xs">
        <h3 className="text-xl font-semibold text-[color:var(--color-on-surface)] tracking-tight">
          {title}
        </h3>
        <p className="text-sm text-[color:var(--color-on-surface-variant)] leading-relaxed">
          {description}
        </p>
      </div>

      {actionLabel && onAction && (
        <Button 
          variant="secondary" 
          onClick={onAction}
          className="mt-4 px-8 py-2.5 rounded-lg border-[color:var(--color-outline-variant)] active:scale-95 transition-all duration-150"
        >
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
