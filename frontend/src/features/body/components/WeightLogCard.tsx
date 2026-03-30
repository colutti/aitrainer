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
        <span className="text-xl font-black text-white tracking-tighter">
          {log.weight_kg.toFixed(1)} <span className="text-[10px] font-bold text-zinc-500 uppercase ml-0.5">kg</span>
        </span>
      )}
      subtitle={hasTrend ? (
        <div className={cn(
          "flex items-center gap-1 text-[10px] font-black px-1.5 py-0.5 rounded uppercase tracking-tighter",
          isTrendUp
            ? "bg-orange-500/10 text-orange-500"
            : "bg-emerald-500/10 text-emerald-500"
        )}>
          {isTrendUp ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
          <span>{(Math.abs(log.weight_kg - (log.trend_weight ?? 0))).toFixed(1)}</span>
        </div>
      ) : undefined}
      metrics={[
        {
          label: t('body.weight.body_fat').split(' ')[0],
          value: log.body_fat_pct ? (
            <span className="text-sm font-black text-white tabular-nums">{log.body_fat_pct.toFixed(1)}<span className="text-[10px] ml-0.5 opacity-50">%</span></span>
          ) : <div className="w-4 h-0.5 bg-white/5 rounded-full mt-2" />,
          valueClassName: 'text-sm font-black text-white tabular-nums',
        },
        {
          label: t('body.weight.muscle_mass').split(' ')[0],
          value: log.muscle_mass_kg ? (
            <span className="text-sm font-black text-white tabular-nums">{log.muscle_mass_kg.toFixed(1)}<span className="text-[10px] ml-0.5 opacity-50">kg</span></span>
          ) : <div className="w-4 h-0.5 bg-white/5 rounded-full mt-2" />,
          valueClassName: 'text-sm font-black text-white tabular-nums',
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
              className="h-10 w-10 rounded-full bg-white/5 text-zinc-500 opacity-0 group-hover:opacity-100 transition-all hover:bg-white/10 hover:text-white"
              title={t('shared.edit')}
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
              className="h-10 w-10 rounded-full bg-red-500/10 text-red-500 opacity-0 group-hover:opacity-100 transition-all hover:bg-red-500/20"
              title={t('shared.delete')}
              aria-label="Delete"
            >
              <Trash2 size={16} />
            </Button>
          )}
        </>
      )}
    />
  );
}
