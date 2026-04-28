import type { ReactNode } from 'react';

import { cn } from '../../utils/cn';

import { PageHeader } from './PageHeader';
import { StickyActionBar } from './StickyActionBar';

interface EntityFormScreenProps {
  title: ReactNode;
  subtitle?: ReactNode;
  form: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function EntityFormScreen({ title, subtitle, form, actions, className }: EntityFormScreenProps) {
  return (
    <div data-testid="entity-form-screen" className={cn('space-y-6', className)}>
      <PageHeader title={title} subtitle={subtitle} />
      <div data-testid="entity-form-body">{form}</div>
      {actions ? <StickyActionBar>{actions}</StickyActionBar> : null}
    </div>
  );
}
