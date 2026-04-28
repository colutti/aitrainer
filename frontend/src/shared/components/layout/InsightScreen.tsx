import type { ReactNode } from 'react';

import { cn } from '../../utils/cn';

import { PageHeader } from './PageHeader';

interface InsightScreenProps {
  title: ReactNode;
  subtitle?: ReactNode;
  metrics?: ReactNode;
  content: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function InsightScreen({
  title,
  subtitle,
  metrics,
  content,
  actions,
  className,
}: InsightScreenProps) {
  return (
    <div data-testid="insight-screen" className={cn('space-y-6', className)}>
      <PageHeader title={title} subtitle={subtitle} actions={actions} />
      {metrics ? <div data-testid="insight-screen-metrics">{metrics}</div> : null}
      <div data-testid="insight-screen-content">{content}</div>
    </div>
  );
}
