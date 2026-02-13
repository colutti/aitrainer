import { Trash2, ChevronRight, Utensils, Flame, Edit2 } from 'lucide-react';

import { Button } from '../../../shared/components/ui/Button';
import { type NutritionLog } from '../../../shared/types/nutrition';
import { formatDate } from '../../../shared/utils/format-date';

interface NutritionLogCardProps {
  log: NutritionLog;
  onDelete?: (id: string) => void;
  onEdit?: (log: NutritionLog) => void;
}

/**
 * NutritionLogCard component
 * 
 * Displays a summary of a daily nutrition log in a list format.
 */
export function NutritionLogCard({ log, onDelete, onEdit }: NutritionLogCardProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(log.id);
    }
  };

  return (
    <div className="bg-dark-card border border-border/50 rounded-2xl p-4 hover:border-gradient-start/40 transition-all duration-300 group flex items-center gap-5 w-full hover:bg-white/5 active:scale-[0.99] relative overflow-hidden">
      {/* Accent Line */}
      <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-start opacity-0 group-hover:opacity-100 transition-opacity" />

      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-gradient-start/10 to-gradient-end/10 flex flex-shrink-0 items-center justify-center text-gradient-start group-hover:scale-110 transition-transform duration-500 shadow-inner">
        <Utensils size={22} />
      </div>
      
      <div className="flex-1 min-w-0 grid grid-cols-1 md:grid-cols-12 gap-4 md:gap-6 items-center">
        {/* Date and Calories Section */}
        <div className="md:col-span-4 min-w-0 flex flex-col justify-center">
           <h3 className="font-black text-text-primary text-base leading-tight tracking-tight group-hover:text-white transition-colors">{formatDate(log.date)}</h3>
           <div className="flex items-center gap-2 mt-1">
              <span className="text-[11px] font-bold text-text-muted flex items-center gap-1.5 uppercase tracking-wider">
                <Flame size={12} className="text-orange-500/70" />
                {log.calories.toLocaleString()} <span className="opacity-50 font-medium">kcal</span>
              </span>
           </div>
        </div>

        {/* Macros Section - Table Style Alignment */}
        <div className="md:col-span-5 grid grid-cols-3 gap-0 md:border-l md:border-white/5 md:pl-6">
             <div className="flex flex-col items-center md:items-end">
                <p className="text-[9px] uppercase font-black text-[#666] tracking-[0.15em] mb-1">Prot</p>
                <p className="text-sm font-black text-emerald-400 tabular-nums">{log.protein_grams.toFixed(1)}<span className="text-[10px] ml-0.5 opacity-60">g</span></p>
             </div>
             <div className="flex flex-col items-center md:items-end border-l border-white/5">
                <p className="text-[9px] uppercase font-black text-[#666] tracking-[0.15em] mb-1">Carb</p>
                <p className="text-sm font-black text-blue-400 tabular-nums">{log.carbs_grams.toFixed(1)}<span className="text-[10px] ml-0.5 opacity-60">g</span></p>
             </div>
             <div className="flex flex-col items-center md:items-end border-l border-white/5">
                <p className="text-[9px] uppercase font-black text-[#666] tracking-[0.15em] mb-1">Gord</p>
                <p className="text-sm font-black text-yellow-400 tabular-nums">{log.fat_grams.toFixed(1)}<span className="text-[10px] ml-0.5 opacity-60">g</span></p>
             </div>
        </div>
        
        {/* Actions - Right */}
        <div className="md:col-span-3 flex justify-end items-center gap-4">
            <div className="flex items-center gap-2">
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={(e) => { e.stopPropagation(); onEdit?.(log); }}
                className="opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-all hover:bg-white/10"
                title="Editar registro"
              >
                <Edit2 size={16} className="text-text-muted hover:text-white" />
              </Button>
              <Button 
                variant="danger" 
                size="icon" 
                onClick={handleDelete}
                className="opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-all hover:scale-110 hover:shadow-red bg-red-500/10 border-red-500/20"
                title="Excluir registro"
              >
                <Trash2 size={16} />
              </Button>
            </div>
            <div className="text-text-muted/30 hidden sm:block group-hover:text-gradient-start group-hover:translate-x-1 transition-all">
              <ChevronRight size={22} />
            </div>
        </div>
      </div>
    </div>
  );
}
