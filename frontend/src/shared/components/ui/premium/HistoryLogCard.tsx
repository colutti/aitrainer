import { ChevronRight } from 'lucide-react';
import type { ReactNode } from 'react';

import { PremiumCard } from './PremiumCard';

export interface HistoryLogMetric {
  label: ReactNode;
  value: ReactNode;
  valueClassName?: string;
  wrapperClassName?: string;
}

export interface HistoryLogCardProps {
  icon: ReactNode;
  title: ReactNode;
  subtitle?: ReactNode;
  leadingMeta?: ReactNode;
  metrics: HistoryLogMetric[];
  notes?: ReactNode;
  actions?: ReactNode;
  onClick?: () => void;
  dataTestId?: string;
  className?: string;
  iconClassName?: string;
}

export function HistoryLogCard({
  icon,
  title,
  subtitle,
  leadingMeta,
  metrics,
  notes,
  actions,
  onClick,
  dataTestId,
  className = '',
  iconClassName = '',
}: HistoryLogCardProps) {
  return (
    <PremiumCard
      onClick={onClick}
      data-testid={dataTestId}
      className={`w-full cursor-pointer border border-white/5 px-4 py-4 md:px-6 md:py-5 ${className}`.trim()}
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex min-w-0 flex-1 items-start gap-3">
          <div className={`mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-zinc-300 ${iconClassName}`.trim()}>
            {icon}
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h3 className="truncate text-base font-bold leading-tight text-white">{title}</h3>
                {(subtitle ?? leadingMeta) && (
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    {subtitle}
                    {leadingMeta}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2">
                {actions}
                <div className="p-1 text-zinc-500">
                  <ChevronRight size={18} />
                </div>
              </div>
            </div>

            <div
              className="mt-3 grid gap-x-4 gap-y-2 sm:grid-cols-2 md:flex md:flex-wrap md:items-center md:gap-5"
              style={{ gridTemplateColumns: metrics.length > 1 ? 'repeat(2, minmax(0, 1fr))' : 'repeat(1, minmax(0, 1fr))' }}
            >
              {metrics.map((metric, index) => (
                <div key={index} className={metric.wrapperClassName}>
                  <div className="mb-0.5 text-[10px] font-semibold uppercase tracking-wide text-zinc-500">{metric.label}</div>
                  <div className={metric.valueClassName}>{metric.value}</div>
                </div>
              ))}
            </div>

            {notes && (
              <div className="mt-3 truncate rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2 text-xs text-zinc-400">
                {notes}
              </div>
            )}
          </div>
        </div>

      </div>
    </PremiumCard>
  );
}
