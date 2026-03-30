import { Check, Dumbbell, AlertCircle, Lock } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { Skeleton } from '../../../shared/components/ui/Skeleton';
import { PREMIUM_UI } from '../../../shared/styles/ui-variants';
import { type TrainerCard } from '../../../shared/types/settings';
import { cn } from '../../../shared/utils/cn';

const TRAINER_COLORS: Record<string, string> = {
  'atlas': 'from-amber-600 to-red-700',
  'luna': 'from-indigo-500 to-purple-600',
  'sargento': 'from-emerald-600 to-teal-800',
  'sofia': 'from-blue-500 to-cyan-600',
  'gymbro': 'from-pink-500 to-rose-600',
};

export interface TrainerSettingsViewProps {
  availableTrainers: TrainerCard[];
  selectedTrainerId: string;
  isSaving: boolean;
  isLoading: boolean;
  isFreePlan: boolean;
  isReadOnly?: boolean;
  onSelect: (id: string) => void;
  onSave: () => void;
  onRetry: () => void;
}

export function TrainerSettingsView({
  availableTrainers,
  selectedTrainerId,
  isSaving,
  isLoading,
  isFreePlan,
  isReadOnly = false,
  onSelect,
  onSave,
  onRetry,
}: TrainerSettingsViewProps) {
  const { t } = useTranslation();

  const getTrainerColor = (id: string) => TRAINER_COLORS[id.toLowerCase()] ?? 'from-zinc-500 to-zinc-700';

  if (isLoading && availableTrainers.length === 0) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="flex items-center gap-4">
           <Skeleton className="w-14 h-14 rounded-2xl bg-white/5" />
           <div className="space-y-2">
              <Skeleton className="h-4 w-32 bg-white/5" />
              <Skeleton className="h-8 w-64 bg-white/5" />
           </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
           {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-48 rounded-[32px] bg-white/5" />)}
        </div>
      </div>
    );
  }

  return (
    <div className={cn(PREMIUM_UI.animation.fadeIn, "space-y-10")}>
      
      {/* HEADER */}
      <div className="flex items-center gap-4">
        <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
          <Dumbbell size={28} />
        </div>
        <div>
          <p className={PREMIUM_UI.text.label}>{t('settings.trainer.subtitle')}</p>
          <h1 className={PREMIUM_UI.text.heading}>{t('settings.trainer.title')}</h1>
        </div>
      </div>

      {/* TRAINERS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {availableTrainers.map((trainer) => {
          const trainerId = trainer.trainer_id.toLowerCase();
          const isLocked = isFreePlan && trainerId !== 'gymbro';
          const isActive = selectedTrainerId === trainer.trainer_id;

          return (
            <PremiumCard
              key={trainer.trainer_id}
              data-testid={`trainer-card-${trainer.trainer_id}`}
              onClick={() => { if (!isReadOnly) onSelect(trainer.trainer_id); }}
              className={cn(
                "p-8 group flex flex-col justify-between min-h-[220px]",
                isReadOnly ? "cursor-default" : "cursor-pointer",
                isActive && "border-indigo-500/50 bg-indigo-500/[0.05] ring-1 ring-indigo-500/20",
                isLocked && "opacity-60 grayscale-[0.5]"
              )}
            >
              <div className="flex items-start justify-between relative z-10">
                <div className="flex items-center gap-5">
                   <div className={cn(
                     "w-20 h-20 rounded-2xl p-0.5 bg-gradient-to-br shadow-inner shrink-0 overflow-hidden",
                     getTrainerColor(trainerId)
                   )}>
                      <img 
                        src={`/assets/avatars/${trainerId}.png`}
                        alt={trainer.name}
                        className="w-full h-full object-cover rounded-[14px]"
                      />
                   </div>
                   <div>
                     <h3 className="font-black text-white text-xl tracking-tight">{trainer.name}</h3>
                     <p className="text-zinc-500 text-xs font-bold mt-1 leading-relaxed uppercase tracking-widest">
                       {t(`landing.trainers.profiles.${trainerId}.tagline`, { defaultValue: trainer.short_description })}
                     </p>
                   </div>
                </div>
                
                <div className="flex items-center gap-3">
                   {isLocked && (
                      <div className="p-2 rounded-xl bg-white/5 border border-white/10 text-zinc-500">
                         <Lock size={16} data-testid="lock-icon" />
                      </div>
                   )}
                   <div className={cn(
                    "w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all",
                    isActive
                      ? "border-indigo-500 bg-indigo-500 text-white shadow-[0_0_15px_rgba(99,102,241,0.4)]"
                      : "border-white/10"
                  )}>
                    {isActive && <Check size={14} strokeWidth={4} data-testid="check-icon" />}
                  </div>
                </div>
              </div>
              
              <div className="mt-6 pt-6 border-t border-white/5">
                  <p className="text-sm text-zinc-400 font-medium italic leading-relaxed">
                    "{t(`landing.trainers.profiles.${trainerId}.catchphrase`, { defaultValue: trainer.catchphrase })}"
                  </p>
              </div>
            </PremiumCard>
          );
        })}
      </div>

      {availableTrainers.length === 0 && !isLoading && (
        <div className="text-center py-20 opacity-40 flex flex-col items-center">
             <AlertCircle className="mx-auto text-red-400 mb-4" size={48} />
             <p className="font-bold text-white">{t('settings.trainer.load_error')}</p>
             <Button type="button" variant="secondary" onClick={onRetry} className="mt-6 px-8 py-3 rounded-full border border-white/10 font-black text-sm uppercase tracking-widest hover:bg-white/5">
                 {t('settings.trainer.retry')}
             </Button>
        </div>
      )}

      {/* FOOTER ACTIONS */}
      <div className="flex justify-end pt-10 border-t border-white/5">
          <Button
            type="button"
            onClick={() => { if (!isReadOnly) onSave(); }} 
            disabled={isReadOnly || isSaving || !selectedTrainerId} 
            className="w-full md:w-auto px-12 py-4 rounded-full bg-white text-black font-black hover:scale-105 active:scale-95 transition-all shadow-xl shadow-white/10 disabled:opacity-50 disabled:scale-100 flex items-center justify-center gap-3"
          >
             {isSaving && !isReadOnly && <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />}
             {isReadOnly ? t('settings.trainer.read_only', 'Somente leitura') : isSaving ? t('settings.trainer.saving') : t('settings.trainer.save_button')}
          </Button>
      </div>
    </div>
  );
}
