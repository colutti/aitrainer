import type { ReactNode } from 'react';

import { cn } from '../../utils/cn';

interface StickyActionBarProps {
  children: ReactNode;
  className?: string;
}

export function StickyActionBar({ children, className }: StickyActionBarProps) {
  return (
    <div
      data-testid="sticky-action-bar"
      className={cn(
        'sticky bottom-0 z-20 mt-6 border-t border-[color:var(--color-app-border)] bg-[color:var(--color-app-bg)]/95 px-0 py-3 backdrop-blur-sm',
        className
      )}
    >
      {children}
    </div>
  );
}
