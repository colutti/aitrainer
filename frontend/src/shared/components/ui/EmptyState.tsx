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
      "flex flex-col items-center justify-center p-8 text-center bg-dark-card/30 border border-white/5 rounded-xl space-y-4",
      className
    )}>
      <div className="w-16 h-16 rounded-xl bg-white/5 flex items-center justify-center text-text-muted/50 mb-2">
        <Icon size={32} />
      </div>
      
      <div className="space-y-2 max-w-xs">
        <h3 className="text-xl font-black text-text-primary tracking-tight">
          {title}
        </h3>
        <p className="text-sm text-text-secondary leading-relaxed">
          {description}
        </p>
      </div>

      {actionLabel && onAction && (
        <Button 
          variant="secondary" 
          onClick={onAction}
          className="mt-4 px-8 py-2.5 rounded-lg bg-white/5 hover:bg-white/10 border-white/5 active:scale-95 transition-all duration-150"
        >
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
