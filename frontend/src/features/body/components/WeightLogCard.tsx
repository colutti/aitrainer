import { Trash2, TrendingUp, TrendingDown, Scale, Edit2, ChevronRight } from 'lucide-react';

import { Button } from '../../../shared/components/ui/Button';
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
 * Displays a weight entry with trend indicators and body composition details.
 */
export function WeightLogCard({ log, onDelete, onEdit, onClick }: WeightLogCardProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(log.date);
    }
  };

  const hasTrend = log.trend_weight !== undefined;
  const isTrendUp = hasTrend && log.weight_kg > (log.trend_weight ?? 0);

  return (
    <div 
      onClick={() => onClick?.(log)}
      className={cn(
        "bg-dark-card border border-border/50 rounded-2xl p-4 hover:border-gradient-start/40 transition-all duration-300 group flex flex-col gap-3 w-full hover:bg-white/5 active:scale-[0.99] relative overflow-hidden",
        onClick && "cursor-pointer"
      )}
    >
      {/* Accent Line */}
      <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-start opacity-0 group-hover:opacity-100 transition-opacity" />

      <div className="flex items-center gap-5 w-full">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-gradient-start/10 to-gradient-end/10 flex flex-shrink-0 items-center justify-center text-gradient-start group-hover:scale-110 transition-transform duration-500 shadow-inner">
          <Scale size={22} />
        </div>
        
        <div className="flex-1 min-w-0 grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
          {/* Date and Weight Section */}
          <div className="md:col-span-4 min-w-0 flex flex-col justify-center">
             <h3 className="font-black text-text-primary text-base leading-tight tracking-tight group-hover:text-white transition-colors">{formatDate(log.date)}</h3>
             <div className="flex items-center gap-3 mt-1">
                <span className="text-xl font-black text-white tracking-tighter">
                  {log.weight_kg.toFixed(1)} <span className="text-[10px] font-bold text-text-muted uppercase ml-0.5">kg</span>
                </span>
                
                {hasTrend && (
                  <div className={cn(
                    "flex items-center gap-1 text-[10px] font-black px-2 py-0.5 rounded-md shadow-sm border",
                    isTrendUp 
                      ? "bg-red-500/5 text-red-500 border-red-500/10" 
                      : "bg-emerald-500/5 text-emerald-500 border-emerald-500/10"
                  )}>
                    {isTrendUp ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                    <span className="tabular-nums">{(Math.abs(log.weight_kg - (log.trend_weight ?? 0))).toFixed(1)}</span>
                  </div>
                )}
             </div>
          </div>

          {/* Body Stats Section - Precise Alignment */}
          <div className="md:col-span-5 grid grid-cols-2 gap-0 md:border-l md:border-white/5 md:pl-6 h-10 items-center">
               <div className="flex flex-col items-center md:items-end pr-4">
                  <p className="text-[9px] uppercase font-black text-[#666] tracking-[0.15em] mb-1">Gordura</p>
                  {log.body_fat_pct ? (
                    <p className="text-sm font-black text-white tabular-nums">{log.body_fat_pct.toFixed(1)}<span className="text-[10px] ml-0.5 opacity-50">%</span></p>
                  ) : <span className="h-5 flex items-center"><div className="w-4 h-0.5 bg-white/5 rounded-full" /></span>}
               </div>
                <div className="flex flex-col items-center md:items-end border-l border-white/5 pl-4">
                  <p className="text-[9px] uppercase font-black text-[#666] tracking-[0.15em] mb-1">Músculo</p>
                  {log.muscle_mass_kg ? (
                    <p className="text-sm font-black text-white tabular-nums">{log.muscle_mass_kg.toFixed(1)}<span className="text-[10px] ml-0.5 opacity-50">kg</span></p>
                  ) : log.muscle_mass_pct ? (
                    <p className="text-sm font-black text-white tabular-nums">{log.muscle_mass_pct.toFixed(1)}<span className="text-[10px] ml-0.5 opacity-50">%</span></p>
                  ) : <span className="h-5 flex items-center"><div className="w-4 h-0.5 bg-white/5 rounded-full" /></span>}
                </div>
          </div>
          
          {/* Actions - Right */}
          <div className="md:col-span-3 flex justify-end items-center gap-3">
              <div className="flex items-center gap-1">
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
              
              {onClick && (
                <div className="text-text-muted/30 ml-2 pl-4 border-l border-white/5 group-hover:text-gradient-start group-hover:translate-x-1 transition-all">
                   <ChevronRight size={22} />
                </div>
              )}
          </div>
        </div>
      </div>
      
      {log.notes && (
        <div className="mt-1 text-xs text-text-secondary border-t border-white/5 pt-2 italic px-2">
          "{log.notes}"
        </div>
      )}

      {(log.neck_cm ?? log.chest_cm ?? log.waist_cm ?? log.hips_cm ?? log.bicep_r_cm ?? log.bicep_l_cm ?? log.thigh_r_cm ?? log.thigh_l_cm ?? log.calf_r_cm ?? log.calf_l_cm ?? log.body_water_pct ?? log.bone_mass_kg ?? log.visceral_fat ?? log.bmr) && (
        <div className="mt-2 text-[10px] text-text-muted border-t border-white/5 pt-3 px-2 flex flex-wrap gap-x-6 gap-y-2">
          <span className="font-black uppercase tracking-widest text-[#555] opacity-50">Detalhes:</span>
          {log.body_water_pct && <span className="flex gap-1">Água <strong className="text-text-secondary">{log.body_water_pct}%</strong></span>}
          {log.bone_mass_kg && <span className="flex gap-1">Óssea <strong className="text-text-secondary">{log.bone_mass_kg}kg</strong></span>}
          {log.visceral_fat && <span className="flex gap-1">Visceral <strong className="text-text-secondary">{log.visceral_fat}</strong></span>}
          {log.bmr && <span className="flex gap-1">TMB <strong className="text-text-secondary">{log.bmr}kcal</strong></span>}
          
          {log.neck_cm && <span className="flex gap-1">Pescoço <strong className="text-text-secondary">{log.neck_cm}cm</strong></span>}
          {log.chest_cm && <span className="flex gap-1">Peito <strong className="text-text-secondary">{log.chest_cm}cm</strong></span>}
          {log.waist_cm && <span className="flex gap-1">Cintura <strong className="text-text-secondary">{log.waist_cm}cm</strong></span>}
          {log.hips_cm && <span className="flex gap-1">Quadril <strong className="text-text-secondary">{log.hips_cm}cm</strong></span>}
          
          {(log.bicep_r_cm ?? log.bicep_l_cm) && (
             <span className="flex gap-1">
               Bíceps <strong className="text-text-secondary">{log.bicep_r_cm && `D:${log.bicep_r_cm.toString()}cm`} {log.bicep_l_cm && `E:${log.bicep_l_cm.toString()}cm`}</strong>
             </span>
          )}
          
          {(log.thigh_r_cm ?? log.thigh_l_cm) && (
              <span className="flex gap-1">
                Coxa <strong className="text-text-secondary">{log.thigh_r_cm && `D:${log.thigh_r_cm.toString()}cm`} {log.thigh_l_cm && `E:${log.thigh_l_cm.toString()}cm`}</strong>
              </span>
           )}
           
           {(log.calf_r_cm ?? log.calf_l_cm) && (
              <span className="flex gap-1">
                Panturrilha <strong className="text-text-secondary">{log.calf_r_cm && `D:${log.calf_r_cm.toString()}cm`} {log.calf_l_cm && `E:${log.calf_l_cm.toString()}cm`}</strong>
              </span>
           )}
        </div>
      )}
    </div>
  );
}
