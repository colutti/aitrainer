import { Trash2, TrendingUp, TrendingDown, Scale, Edit2, ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { type WeightLog } from '../../../shared/types/body';
import { cn } from '../../../shared/utils/cn';
import { formatDate } from '../../../shared/utils/format-date';

interface WeightLogCardProps {
  log: WeightLog;
  onDelete?: (date: string) => void;
  onEdit?: (log: WeightLog) => void;
  onClick?: (log: WeightLog) => void;
}

/**
 * WeightLogCard component
 * 
 * Displays a weight entry with premium Glassmorphism aesthetic.
 */
export function WeightLogCard({ log, onDelete, onEdit, onClick }: WeightLogCardProps) {
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
    <PremiumCard 
      onClick={() => onClick?.(log)}
      data-testid="weight-log-card"
      className="p-5 md:p-6 cursor-pointer group flex flex-col gap-4 w-full"
    >
      <div className="flex items-center gap-4 w-full">
        <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-white/5 flex shrink-0 items-center justify-center text-indigo-400 group-hover:text-emerald-400 transition-colors shadow-inner">
          <Scale size={24} />
        </div>
        
        <div className="flex-1 min-w-0 grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
          {/* Date and Weight */}
          <div className="md:col-span-4 min-w-0">
             <h3 className="font-black text-white text-base leading-tight tracking-tight">{formatDate(log.date)}</h3>
             <div className="flex items-center gap-3 mt-1">
                <span className="text-xl font-black text-white tracking-tighter">
                  {log.weight_kg.toFixed(1)} <span className="text-[10px] font-bold text-zinc-500 uppercase ml-0.5">kg</span>
                </span>
                
                {hasTrend && (
                  <div className={cn(
                    "flex items-center gap-1 text-[10px] font-black px-1.5 py-0.5 rounded uppercase tracking-tighter",
                    isTrendUp 
                      ? "bg-orange-500/10 text-orange-500" 
                      : "bg-emerald-500/10 text-emerald-500"
                  )}>
                    {isTrendUp ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                    <span>{(Math.abs(log.weight_kg - (log.trend_weight ?? 0))).toFixed(1)}</span>
                  </div>
                )}
             </div>
          </div>

          {/* Composition Stats */}
           <div className="md:col-span-5 grid grid-cols-2 gap-4 md:border-l border-white/5 md:pl-6">
                <div>
                   <p className="text-[9px] uppercase font-black text-zinc-600 tracking-widest mb-0.5">{t('body.weight.body_fat').split(' ')[0]}</p>
                  {log.body_fat_pct ? (
                    <p className="text-sm font-black text-white tabular-nums">{log.body_fat_pct.toFixed(1)}<span className="text-[10px] ml-0.5 opacity-50">%</span></p>
                   ) : <div className="w-4 h-0.5 bg-white/5 rounded-full mt-2" />}
                </div>
                 <div>
                   <p className="text-[9px] uppercase font-black text-zinc-600 tracking-widest mb-0.5">{t('body.weight.muscle_mass').split(' ')[0]}</p>
                  {log.muscle_mass_kg ? (
                    <p className="text-sm font-black text-white tabular-nums">{log.muscle_mass_kg.toFixed(1)}<span className="text-[10px] ml-0.5 opacity-50">kg</span></p>
                  ) : <div className="w-4 h-0.5 bg-white/5 rounded-full mt-2" />}
                </div>
          </div>
          
          {/* Actions */}
          <div className="md:col-span-3 flex justify-end items-center gap-2">
              {onEdit && (
                <button 
                  onClick={(e) => { e.stopPropagation(); onEdit(log); }}
                  className="p-2.5 rounded-full bg-white/5 text-zinc-500 opacity-0 group-hover:opacity-100 transition-all hover:bg-white/10 hover:text-white"
                  title={t('shared.edit')}
                >
                  <Edit2 size={16} />
                </button>
              )}
              {onDelete && (
                <button 
                  onClick={handleDelete}
                  data-testid="btn-delete-weight"
                  className="p-2.5 rounded-full bg-red-500/10 text-red-500 opacity-0 group-hover:opacity-100 transition-all hover:bg-red-500/20"
                  title={t('shared.delete')}
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
      </div>
      
      {log.notes && (
        <div className="text-[11px] text-zinc-500 italic bg-black/20 p-2 rounded-xl border border-white/5">
          "{log.notes}"
        </div>
      )}
    </PremiumCard>
  );
}
