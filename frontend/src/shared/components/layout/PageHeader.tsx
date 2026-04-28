import type { ReactNode } from 'react';

import { cn } from '../../utils/cn';

interface PageHeaderProps {
  title: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function PageHeader({ title, subtitle, actions, className }: PageHeaderProps) {
  return (
    <header
      data-testid="page-header"
        className={cn(
        'flex flex-col gap-4 border-b border-[color:var(--color-outline-variant)] pb-4 md:flex-row md:items-start md:justify-between',
        className
      )}
    >
      <div className="min-w-0">
        <h1 data-testid="page-header-title" className="text-2xl font-semibold tracking-tight">
          {title}
        </h1>
        {subtitle ? (
          <p data-testid="page-header-subtitle" className="mt-1 text-sm text-[color:var(--color-on-surface-variant)]">
            {subtitle}
          </p>
        ) : null}
      </div>
      {actions ? (
        <div data-testid="page-header-actions" className="shrink-0">
          {actions}
        </div>
      ) : null}
    </header>
  );
}
