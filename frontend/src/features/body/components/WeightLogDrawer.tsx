import { X, Scale, Activity, Ruler, FileText, Droplets, Zap, Target, Bone, Flame } from 'lucide-react';

import { Button } from '../../../shared/components/ui/Button';
import type { WeightLog } from '../../../shared/types/body';
import { cn } from '../../../shared/utils/cn';
import { formatDate } from '../../../shared/utils/format-date';

interface WeightLogDrawerProps {
  log: WeightLog | null;
  isOpen: boolean;
  onClose: () => void;
}

/**
 * Drawer component to display detailed weight log information
 * Slides in from the right side of the screen
 */
export function WeightLogDrawer({ log, isOpen, onClose }: WeightLogDrawerProps) {
  if (!log) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className={cn(
          'fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity',
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className={cn(
          'fixed right-0 top-0 h-full w-full md:w-[500px] bg-dark-card border-l border-border z-50',
          'transform transition-transform duration-300 ease-in-out overflow-y-auto',
          isOpen ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        {/* Header */}
        <div className="sticky top-0 bg-dark-card/95 backdrop-blur-md border-b border-border p-6 flex items-center justify-between z-10">
          <div>
            <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
              <Scale className="text-gradient-start" size={24} />
              Detalhes do Registro
            </h2>
            <p className="text-sm text-text-secondary mt-1 capitalize">
              {formatDate(log.date)}
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-text-muted hover:text-text-primary"
          >
            <X size={20} />
          </Button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-8">
          
          {/* Main Weight Display */}
          <div className="flex items-center justify-between bg-zinc-900/50 p-6 rounded-2xl border border-white/5">
            <div>
              <p className="text-sm text-text-muted mb-1 font-medium uppercase tracking-wider">Peso Registrado</p>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-black text-white">{log.weight_kg.toFixed(1)}</span>
                <span className="text-xl text-text-secondary font-medium">kg</span>
              </div>
            </div>
            {log.trend_weight !== undefined && (
              <div className="text-right">
                 <p className="text-xs text-text-muted mb-1 font-medium uppercase tracking-wider">Tendência</p>
                 <div className={cn(
                   "text-lg font-bold flex items-center justify-end gap-1",
                   log.weight_kg > (log.trend_weight || 0) ? "text-red-400" : "text-emerald-400"
                 )}>
                    {log.weight_kg > (log.trend_weight || 0) ? '▲' : '▼'}
                    {Math.abs(log.weight_kg - (log.trend_weight || 0)).toFixed(1)}kg
                 </div>
              </div>
            )}
          </div>

          {/* Body Composition Grid */}
          {(log.body_fat_pct != null || log.muscle_mass_pct != null || log.muscle_mass_kg != null || log.body_water_pct != null || log.bone_mass_kg != null || log.visceral_fat != null || log.bmr != null || log.bmi != null) && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 pb-2 border-b border-white/5">
                <Activity className="text-blue-400" size={18} />
                <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
                  Composição Corporal
                </h3>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                {log.body_fat_pct != null && (
                  <div className="bg-zinc-900/30 p-3 rounded-xl border border-white/5">
                    <div className="flex items-center gap-2 mb-1">
                      <Target size={14} className="text-orange-400" />
                      <p className="text-[10px] text-text-muted font-bold uppercase">Gordura</p>
                    </div>
                    <p className="text-xl font-bold text-text-primary">{log.body_fat_pct}%</p>
                  </div>
                )}
                
                {(log.muscle_mass_pct != null || log.muscle_mass_kg != null) && (
                  <div className="bg-zinc-900/30 p-3 rounded-xl border border-white/5">
                    <div className="flex items-center gap-2 mb-1">
                      <Zap size={14} className="text-yellow-400" />
                      <p className="text-[10px] text-text-muted font-bold uppercase">Massa Muscular</p>
                    </div>
                    {log.muscle_mass_kg != null ? (
                      <p className="text-xl font-bold text-text-primary">{log.muscle_mass_kg}kg</p>
                    ) : (
                      <p className="text-xl font-bold text-text-primary">{log.muscle_mass_pct}%</p>
                    )}
                  </div>
                )}

                {log.body_water_pct != null && (
                  <div className="bg-zinc-900/30 p-3 rounded-xl border border-white/5">
                    <div className="flex items-center gap-2 mb-1">
                       <Droplets size={14} className="text-blue-400" />
                       <p className="text-[10px] text-text-muted font-bold uppercase">Água Corporal</p>
                    </div>
                    <p className="text-xl font-bold text-text-primary">{log.body_water_pct}%</p>
                  </div>
                )}

                {log.bone_mass_kg != null && (
                  <div className="bg-zinc-900/30 p-3 rounded-xl border border-white/5">
                    <div className="flex items-center gap-2 mb-1">
                       <Bone size={14} className="text-zinc-400" />
                       <p className="text-[10px] text-text-muted font-bold uppercase">Massa Óssea</p>
                    </div>
                    <p className="text-xl font-bold text-text-primary">{log.bone_mass_kg}kg</p>
                  </div>
                )}

                {log.visceral_fat != null && (
                  <div className="bg-zinc-900/30 p-3 rounded-xl border border-white/5">
                    <div className="flex items-center gap-2 mb-1">
                       <Activity size={14} className="text-red-400" />
                       <p className="text-[10px] text-text-muted font-bold uppercase">Gordura Visceral</p>
                    </div>
                    <p className="text-xl font-bold text-text-primary">{log.visceral_fat}</p>
                  </div>
                )}

                {log.bmr != null && (
                   <div className="bg-zinc-900/30 p-3 rounded-xl border border-white/5">
                    <div className="flex items-center gap-2 mb-1">
                       <Flame className="text-orange-500" size={14} />
                       <p className="text-[10px] text-text-muted font-bold uppercase">Taxa Metabólica</p>
                    </div>
                    <p className="text-xl font-bold text-text-primary">{log.bmr} kcal</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Measurements Grid - Always visible */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-white/5">
              <Ruler className="text-emerald-400" size={18} />
              <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
                Medidas (cm)
              </h3>
            </div>

             <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {[
                  { label: 'Pescoço', value: log.neck_cm },
                  { label: 'Peito', value: log.chest_cm },
                  { label: 'Cintura', value: log.waist_cm },
                  { label: 'Quadril', value: log.hips_cm },
                  { label: 'Bíceps (D)', value: log.bicep_r_cm },
                  { label: 'Bíceps (E)', value: log.bicep_l_cm },
                  { label: 'Coxa (D)', value: log.thigh_r_cm },
                  { label: 'Coxa (E)', value: log.thigh_l_cm },
                  { label: 'Panturrilha (D)', value: log.calf_r_cm },
                  { label: 'Panturrilha (E)', value: log.calf_l_cm },
                ].map((item) => (
                  <div key={item.label} className={cn(
                    "px-3 py-2 rounded-lg border flex justify-between items-center transition-colors",
                    item.value 
                      ? "bg-zinc-900/30 border-white/5" 
                      : "bg-zinc-900/10 border-white/5 opacity-50"
                  )}>
                    <span className="text-xs text-text-muted">{item.label}</span>
                    <span className={cn(
                      "font-mono font-bold",
                      item.value ? "text-text-primary" : "text-text-muted/50"
                    )}>
                      {item.value ?? '-'}
                    </span>
                  </div>
                ))}
             </div>
          </div>

          {/* Notes */}
          {log.notes && (
            <div className="space-y-4">
               <div className="flex items-center gap-2 pb-2 border-b border-white/5">
                <FileText className="text-purple-400" size={18} />
                <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
                  Observações
                </h3>
              </div>
              <div className="bg-zinc-900/30 p-4 rounded-xl border border-white/5 text-sm text-text-secondary italic leading-relaxed">
                "{log.notes}"
              </div>
            </div>
          )}

        </div>
      </div>
    </>
  );
}
