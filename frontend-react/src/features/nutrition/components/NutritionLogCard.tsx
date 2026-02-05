import { Trash2, ChevronRight, Utensils } from 'lucide-react';

import { Button } from '../../../shared/components/ui/Button';
import { type NutritionLog } from '../../../shared/types/nutrition';
import { formatDate } from '../../../shared/utils/format-date';

interface NutritionLogCardProps {
  log: NutritionLog;
  onDelete?: (id: string) => void;
}

/**
 * NutritionLogCard component
 * 
 * Displays a summary of a daily nutrition log in a list format.
 */
export function NutritionLogCard({ log, onDelete }: NutritionLogCardProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(log.id);
    }
  };

  return (
    <div className="bg-dark-card border border-border rounded-2xl p-4 hover:border-gradient-start/30 transition-all group flex items-center gap-4">
      <div className="w-12 h-12 rounded-xl bg-gradient-start/10 flex items-center justify-center text-gradient-start group-hover:scale-110 transition-transform">
        <Utensils size={20} />
      </div>
      
      <div className="flex-1 min-w-0">
        <h3 className="font-bold text-text-primary truncate">{formatDate(log.date)}</h3>
        <div className="flex items-center gap-3 mt-1">
          <span className="text-xs bg-dark-bg px-2 py-0.5 rounded-full border border-border text-text-secondary">
            {log.calories.toString()} kcal
          </span>
          <div className="flex gap-2 text-[10px] font-bold uppercase tracking-tight text-text-muted">
            <span>P: {log.protein_grams.toString()}g</span>
            <span>C: {log.carbs_grams.toString()}g</span>
            <span>G: {log.fat_grams.toString()}g</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button 
          variant="danger" 
          size="icon" 
          onClick={handleDelete}
          className="opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <Trash2 size={16} />
        </Button>
        <ChevronRight size={20} className="text-text-tertiary" />
      </div>
    </div>
  );
}
