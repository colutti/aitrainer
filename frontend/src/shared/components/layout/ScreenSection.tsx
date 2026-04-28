import type { ReactNode } from 'react';

import { cn } from '../../utils/cn';

interface ScreenSectionProps {
  children: ReactNode;
  title?: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function ScreenSection({ children, title, description, actions, className }: ScreenSectionProps) {
  return (
    <section
      data-testid="screen-section"
      className={cn(
        'rounded-[var(--radius-lg)] border border-[color:var(--color-app-border)] bg-[color:var(--color-surface-container)] p-4 md:p-6',
        className
      )}
    >
      {title || description || actions ? (
        <div className="mb-4 flex flex-col gap-2 md:mb-5 md:flex-row md:items-start md:justify-between">
          <div className="min-w-0">
            {title ? <h2 data-testid="screen-section-title" className="text-base font-semibold">{title}</h2> : null}
            {description ? (
              <p data-testid="screen-section-description" className="text-sm text-[color:var(--color-text-secondary)]">
                {description}
              </p>
            ) : null}
          </div>
          {actions ? <div data-testid="screen-section-actions">{actions}</div> : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}
