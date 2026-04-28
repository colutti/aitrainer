import type { ReactNode } from 'react';

import { cn } from '../../utils/cn';

interface AppShellProps {
  children: ReactNode;
  className?: string;
  testId?: string;
}

export function AppShell({ children, className, testId = 'app-shell' }: AppShellProps) {
  return (
    <div
      data-testid={testId}
      className={cn(
        'min-h-[100dvh] bg-[color:var(--color-background)] text-[color:var(--color-on-background)]',
        className
      )}
    >
      {children}
    </div>
  );
}
