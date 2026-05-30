import { Trash2, TrendingUp, TrendingDown, Scale, Edit2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { HistoryLogCard } from '../../../shared/components/ui/premium/HistoryLogCard';
import { type WeightLog } from '../../../shared/types/body';
import { cn } from '../../../shared/utils/cn';
import { formatDate } from '../../../shared/utils/format-date';

interface WeightLogCardProps {
  log: WeightLog;
  isReadOnly?: boolean;
  onDelete?: (date: string) => void;
  onEdit?: (log: WeightLog) => void;
  onClick?: (log: WeightLog) => void;
}

/**
 * WeightLogCard component
 * 
 * Displays a weight entry with premium Glassmorphism aesthetic.
 */
export function WeightLogCard({ log, isReadOnly = false, onDelete, onEdit, onClick }: WeightLogCardProps) {
  const { t } = useTranslation();
  const muscleMassValue = log.muscle_mass_kg ?? log.muscle_mass_pct;
  const muscleMassUnit = 'kg';
  
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(log.date);
    }
  };

  const hasTrend = log.trend_weight != null;
  const isTrendUp = hasTrend && log.weight_kg > (log.trend_weight ?? 0);

  return (
    <HistoryLogCard
      dataTestId="weight-log-card"
      onClick={() => { onClick?.(log); }}
      icon={<Scale size={24} />}
      title={formatDate(log.date)}
      leadingMeta={(
        <span className="text-xl font-semibold text-text-primary tracking-tighter">
          {log.weight_kg.toFixed(1)} <span className="text-[10px] font-bold text-text-muted uppercase ml-0.5">kg</span>
        </span>
      )}
      subtitle={hasTrend ? (
        <div className={cn(
          "flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.5 rounded uppercase tracking-tighter",
          isTrendUp
            ? "bg-[color:var(--color-tertiary)]/10 text-[color:var(--color-tertiary)]"
            : "bg-[color:var(--color-secondary)]/10 text-[color:var(--color-secondary)]"
        )}>
          {isTrendUp ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
          <span>{(Math.abs(log.weight_kg - (log.trend_weight ?? 0))).toFixed(1)}</span>
        </div>
      ) : undefined}
      metrics={[
        {
          label: t('body.weight.body_fat').split(' ')[0],
          value: log.body_fat_pct ? (
            <span className="text-sm font-semibold text-text-primary tabular-nums">{log.body_fat_pct.toFixed(1)}<span className="text-[10px] ml-0.5 opacity-50">%</span></span>
          ) : <div className="w-4 h-0.5 bg-[color:var(--color-surface-container)] rounded-full mt-2" />,
          valueClassName: 'text-sm font-semibold text-text-primary tabular-nums',
        },
        {
          label: t('body.weight.muscle_mass').split(' ')[0],
          value: muscleMassValue != null ? (
            <span className="text-sm font-semibold text-text-primary tabular-nums">{muscleMassValue.toFixed(1)}<span className="text-[10px] ml-0.5 opacity-50">{muscleMassUnit}</span></span>
          ) : <div className="w-4 h-0.5 bg-[color:var(--color-surface-container)] rounded-full mt-2" />,
          valueClassName: 'text-sm font-semibold text-text-primary tabular-nums',
        },
      ]}
      notes={log.notes ? `"${log.notes}"` : undefined}
      actions={(
        <>
          {!isReadOnly && onEdit && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={(e) => { e.stopPropagation(); onEdit(log); }}
              className="h-9 w-9 rounded-full text-text-secondary hover:bg-[color:var(--color-surface-container-high)] hover:text-text-primary"
              title={t('shared.edit')}
              aria-label={t('shared.edit')}
            >
              <Edit2 size={16} />
            </Button>
          )}
          {!isReadOnly && onDelete && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={handleDelete}
              data-testid="btn-delete-weight"
              className="h-9 w-9 rounded-full text-red-300 hover:bg-red-500/15 hover:text-red-100"
              title={t('shared.delete')}
              aria-label={t('shared.delete')}
            >
              <Trash2 size={16} />
            </Button>
          )}
        </>
      )}
    />
  );
}
