import type { PropsWithChildren } from 'react';

export function DashboardWorkspaceSection({ children }: PropsWithChildren) {
  return (
    <div data-testid="dashboard-workspace" className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.75fr)] gap-6">
      {children}
    </div>
  );
}
