import type { ReactNode } from 'react';

import { cn } from '../../utils/cn';

import { ListToolbar } from './ListToolbar';
import { PageHeader } from './PageHeader';

interface EntityListScreenProps {
  title: ReactNode;
  subtitle?: ReactNode;
  toolbar?: ReactNode;
  list: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function EntityListScreen({
  title,
  subtitle,
  toolbar,
  list,
  actions,
  className,
}: EntityListScreenProps) {
  return (
    <div data-testid="entity-list-screen" className={cn('space-y-6', className)}>
      <PageHeader title={title} subtitle={subtitle} actions={actions} />
      {toolbar ? <ListToolbar>{toolbar}</ListToolbar> : null}
      <div data-testid="entity-list-body">{list}</div>
    </div>
  );
}
