import { Trash2, ChevronRight, Utensils, Flame, Edit2 } from 'lucide-react';

import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { type NutritionLog } from '../../../shared/types/nutrition';
import { formatDate } from '../../../shared/utils/format-date';

interface NutritionLogCardProps {
  log: NutritionLog;
  onDelete?: (id: string) => void;
  onEdit?: (log: NutritionLog) => void;
  onClick?: (log: NutritionLog) => void;
}

/**
 * NutritionLogCard component
 * 
 * Displays a summary of a nutrition log entry with premium Glassmorphism aesthetic.
 */
export function NutritionLogCard({ log, onDelete, onEdit, onClick }: NutritionLogCardProps) {
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
    <PremiumCard 
      onClick={() => { onClick?.(log); }}
      data-testid="nutrition-log-card"
      className="p-4 md:p-5 cursor-pointer group flex items-center gap-4 w-full"
    >
      <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-white/5 flex shrink-0 items-center justify-center text-indigo-400 group-hover:text-emerald-400 transition-colors shadow-inner">
        <Utensils size={22} />
      </div>
      
      <div className="flex-1 min-w-0 grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
        {/* Date and Title */}
        <div className="md:col-span-4 min-w-0">
           <h3 className="font-black text-white text-base leading-tight tracking-tight">{formatDate(log.date)}</h3>
           <div className="flex items-center gap-2 mt-1">
              <span className="text-[10px] font-black text-orange-400 bg-orange-400/10 px-1.5 py-0.5 rounded flex items-center gap-1 uppercase tracking-wider">
                <Flame size={10} fill="currentColor" />
                {log.calories.toLocaleString()} kcal
              </span>
           </div>
        </div>

        {/* Macros Section */}
        <div className="md:col-span-5 grid grid-cols-3 gap-4 md:border-l border-white/5 md:pl-6">
             <div className="text-center md:text-left">
                <p className="text-[9px] uppercase font-black text-zinc-600 tracking-widest mb-0.5">Prot</p>
                <p className="text-sm font-black text-emerald-400 tabular-nums">{Math.round(log.protein_grams)}g</p>
             </div>
             <div className="text-center md:text-left border-l border-white/5 pl-4 md:pl-0 md:border-0">
                <p className="text-[9px] uppercase font-black text-zinc-600 tracking-widest mb-0.5">Carb</p>
                <p className="text-sm font-black text-blue-400 tabular-nums">{Math.round(log.carbs_grams)}g</p>
             </div>
             <div className="text-center md:text-left border-l border-white/5 pl-4 md:pl-0 md:border-0">
                <p className="text-[9px] uppercase font-black text-zinc-600 tracking-widest mb-0.5">Gord</p>
                <p className="text-sm font-black text-orange-400 tabular-nums">{Math.round(log.fat_grams)}g</p>
             </div>
        </div>
        
        {/* Actions */}
        <div className="md:col-span-3 flex justify-end items-center gap-2">
            {onEdit && (
              <button 
                onClick={handleEdit}
                className="p-2.5 rounded-full bg-white/5 text-zinc-500 opacity-0 group-hover:opacity-100 transition-all hover:bg-white/10 hover:text-white"
                title="Editar registro"
              >
                <Edit2 size={16} />
              </button>
            )}
            {onDelete && (
              <button 
                onClick={handleDelete}
                data-testid="btn-delete-nutrition"
                className="p-2.5 rounded-full bg-red-500/10 text-red-500 opacity-0 group-hover:opacity-100 transition-all hover:bg-red-500/20"
                title="Excluir registro"
                aria-label="Delete"
              >
                <Trash2 size={16} />
              </button>
            )}
            <div className="p-2 text-zinc-700 group-hover:text-white transition-colors">
              <ChevronRight size={20} />
            </div>
        </div>
      </div>
    </PremiumCard>
  );
}
