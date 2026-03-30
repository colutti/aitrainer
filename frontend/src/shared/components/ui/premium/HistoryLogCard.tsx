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
      className={`p-5 md:p-6 cursor-pointer group flex flex-col gap-4 w-full ${className}`.trim()}
    >
      <div className="flex items-start gap-4">
        <div className={`w-12 h-12 rounded-2xl bg-zinc-900 border border-white/5 flex shrink-0 items-center justify-center text-indigo-400 group-hover:text-emerald-400 transition-colors shadow-inner ${iconClassName}`.trim()}>
          {icon}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 className="font-black text-white text-base leading-tight tracking-tight">{title}</h3>
              {(subtitle ?? leadingMeta) && (
                <div className="flex flex-wrap items-center gap-2 mt-1">
                  {subtitle}
                  {leadingMeta}
                </div>
              )}
            </div>

            <div className="flex items-center gap-2 shrink-0">
              {actions}
              <div className="p-2 text-zinc-700 group-hover:text-white transition-colors">
                <ChevronRight size={20} />
              </div>
            </div>
          </div>

          <div
            className="mt-4 grid gap-3 rounded-2xl border border-white/5 bg-white/[0.02] p-3"
            style={{ gridTemplateColumns: `repeat(${String(Math.max(1, metrics.length))}, minmax(0, 1fr))` }}
          >
            {metrics.map((metric, index) => (
              <div key={index} className={metric.wrapperClassName}>
                <div className="text-[9px] uppercase font-black text-zinc-600 tracking-widest mb-0.5">{metric.label}</div>
                <div className={metric.valueClassName}>{metric.value}</div>
              </div>
            ))}
          </div>

          {notes && (
            <div className="text-[11px] text-zinc-500 italic bg-black/20 p-2 rounded-xl border border-white/5 mt-4">
              {notes}
            </div>
          )}
        </div>
      </div>
    </PremiumCard>
  );
}
