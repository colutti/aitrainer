import { Check } from 'lucide-react';

import { cn } from '../../utils/cn';
import { Button } from '../ui/Button';

export interface PlanCardData {
  id: string;
  name: string;
  subtitle: string;
  priceLabel: string;
  features: string[];
  badge?: string;
  highlight?: boolean;
}

export interface PlanCardProps {
  plan: PlanCardData;
  context: 'marketing' | 'selection' | 'management';
  actionLabel: string;
  onAction?: () => void;
  selected?: boolean;
  current?: boolean;
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  actionTestId?: string;
}

export function PlanCard({
  plan,
  context,
  actionLabel,
  onAction,
  selected = false,
  current = false,
  disabled = false,
  loading = false,
  className,
  actionTestId,
}: PlanCardProps) {
  const isHighlighted = (plan.highlight ?? false) || current || selected;

  return (
    <div
      className={cn(
        'flex flex-col p-8 rounded-2xl border bg-[color:var(--color-background)]',
        isHighlighted ? 'border-[color:var(--color-primary)]/60 ring-1 ring-[color:var(--color-primary)]/30' : 'border-[color:var(--color-outline-variant)]',
        context === 'selection' && 'cursor-pointer',
        className
      )}
    >
      <div className="mb-6">
        {plan.badge ? (
          <span className="inline-flex mb-4 rounded-full border border-[color:var(--color-primary)]/30 bg-[color:var(--color-primary)]/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-[color:var(--color-primary)]">
            {plan.badge}
          </span>
        ) : null}
        <h3 className="text-xl font-bold text-text-primary">{plan.name}</h3>
        <p className="mt-2 min-h-[40px] text-sm text-text-secondary">{plan.subtitle}</p>
      </div>

      <div className="mb-8">
        <span className="text-3xl font-bold text-text-primary">{plan.priceLabel}</span>
      </div>

      <Button
        onClick={onAction}
        disabled={disabled || loading}
        isLoading={loading}
        fullWidth
        className={cn(
          'mb-8 rounded-md',
          isHighlighted ? 'shadow-none' : 'border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)]'
        )}
        data-testid={actionTestId}
      >
        {actionLabel}
      </Button>

      <ul className="space-y-3">
        {plan.features.map((feature) => (
          <li key={`${plan.id}-${feature}`} className="flex items-start gap-3 text-sm text-text-secondary">
            <Check className="mt-0.5 h-4 w-4 shrink-0 text-[color:var(--color-primary)]" />
            <span>{feature}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
