import type { ReactNode } from 'react';

import { cn } from '../../utils/cn';

interface ListToolbarProps {
  children?: ReactNode;
  leftSlot?: ReactNode;
  rightSlot?: ReactNode;
  className?: string;
}

export function ListToolbar({ children, leftSlot, rightSlot, className }: ListToolbarProps) {
  return (
    <div
      data-testid="list-toolbar"
      className={cn(
        'flex flex-col gap-3 rounded-[var(--radius-md)] border border-[color:var(--color-app-border)] bg-[color:var(--color-surface-container-low)] p-3 md:flex-row md:items-center md:justify-between',
        className
      )}
    >
      {children ?? (
        <>
          <div data-testid="list-toolbar-left" className="min-w-0">{leftSlot}</div>
          <div data-testid="list-toolbar-right" className="shrink-0">{rightSlot}</div>
        </>
      )}
    </div>
  );
}
