import { Trash2, Utensils, Flame, Edit2 } from 'lucide-react';

import { Button } from '../../../shared/components/ui/Button';
import { HistoryLogCard } from '../../../shared/components/ui/premium/HistoryLogCard';
import { type NutritionLog } from '../../../shared/types/nutrition';
import { formatDate } from '../../../shared/utils/format-date';

interface NutritionLogCardProps {
  log: NutritionLog;
  isReadOnly?: boolean;
  onDelete?: (id: string) => void;
  onEdit?: (log: NutritionLog) => void;
  onClick?: (log: NutritionLog) => void;
}

/**
 * NutritionLogCard component
 * 
 * Displays a summary of a nutrition log entry with premium Glassmorphism aesthetic.
 */
export function NutritionLogCard({ log, isReadOnly = false, onDelete, onEdit, onClick }: NutritionLogCardProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(log.id);
    }
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onEdit) {
      onEdit(log);
    }
  };

  return (
    <HistoryLogCard
      dataTestId="nutrition-log-card"
      icon={<Utensils size={22} />}
      title={formatDate(log.date)}
      leadingMeta={(
        <span className="text-[10px] font-black text-orange-400 bg-orange-400/10 px-1.5 py-0.5 rounded flex items-center gap-1 uppercase tracking-wider">
          <Flame size={10} fill="currentColor" />
          {log.calories.toLocaleString()} kcal
        </span>
      )}
      metrics={[
        {
          label: 'Prot',
          value: <p className="text-sm font-black text-emerald-400 tabular-nums">{Math.round(log.protein_grams)}g</p>,
        },
        {
          label: 'Carb',
          value: <p className="text-sm font-black text-blue-400 tabular-nums">{Math.round(log.carbs_grams)}g</p>,
        },
        {
          label: 'Gord',
          value: <p className="text-sm font-black text-orange-400 tabular-nums">{Math.round(log.fat_grams)}g</p>,
        },
      ]}
      notes={log.notes ? `"${log.notes}"` : undefined}
      onClick={() => { if (!isReadOnly) onClick?.(log); }}
      actions={(
        <>
          {!isReadOnly && onEdit && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={handleEdit}
              className="h-10 w-10 rounded-full bg-white/5 text-zinc-500 opacity-0 group-hover:opacity-100 transition-all hover:bg-white/10 hover:text-white"
              title="Editar registro"
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
              data-testid="btn-delete-nutrition"
              className="h-10 w-10 rounded-full bg-red-500/10 text-red-500 opacity-0 group-hover:opacity-100 transition-all hover:bg-red-500/20"
              title="Excluir registro"
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
