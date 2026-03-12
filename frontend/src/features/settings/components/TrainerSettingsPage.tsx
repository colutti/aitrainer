import { Check, Dumbbell, AlertCircle, Lock } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { Skeleton } from '../../../shared/components/ui/Skeleton';
import { useAuthStore } from '../../../shared/hooks/useAuth';
import { useNotificationStore } from '../../../shared/hooks/useNotification';
import { useSettingsStore } from '../../../shared/hooks/useSettings';
import { cn } from '../../../shared/utils/cn';

const TRAINER_COLORS: Record<string, string> = {
  'atlas': 'from-amber-600 to-red-700',
  'luna': 'from-indigo-500 to-purple-600',
  'sargento': 'from-emerald-600 to-teal-800',
  'sofia': 'from-blue-500 to-cyan-600',
  'gymbro': 'from-pink-500 to-rose-600',
};

export function TrainerSettingsPage() {
  const { t } = useTranslation();
  const { 
    trainer, 
    availableTrainers, 
    isLoading, 
    isSaving,
    fetchTrainer, 
    fetchAvailableTrainers, 
    updateTrainer 
  } = useSettingsStore();
  
  const notify = useNotificationStore();
  const { userInfo } = useAuthStore();
  const [selectedTrainerId, setSelectedTrainerId] = useState<string>('');

  const isFreePlan = userInfo?.subscription_plan === 'Free' || userInfo?.subscription_plan === 'FREE';

  useEffect(() => {
    void fetchAvailableTrainers();
    void fetchTrainer();
  }, [fetchAvailableTrainers, fetchTrainer]);

  useEffect(() => {
    if (trainer) {
      // eslint-disable-next-line
      setSelectedTrainerId(trainer.trainer_type);
    }
  }, [trainer]);

  const handleSave = async () => {
    if (!selectedTrainerId) return;
    try {
      await updateTrainer(selectedTrainerId);
      notify.success(t('settings.trainer.update_success'));
    } catch {
      notify.error(t('settings.trainer.update_error'));
    }
  };

  const getTrainerColor = (id: string) => TRAINER_COLORS[id] ?? 'from-gray-500 to-gray-700';

  if (isLoading && availableTrainers.length === 0) {
    return (
        <div className="max-w-6xl mx-auto space-y-6 p-4">
             <div className="flex gap-4 mb-8">
                <Skeleton className="w-16 h-16 rounded-xl" />
                <div className="space-y-2">
                    <Skeleton className="h-8 w-48" />
                    <Skeleton className="h-4 w-64" />
                </div>
             </div>
             <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[1, 2, 3, 4].map(i => (
                    <Skeleton key={i} className="h-40 w-full rounded-xl" />
                ))}
            </div>
        </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-700 h-full overflow-y-auto pb-20">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-gradient-start/10 rounded-xl">
            <Dumbbell className="text-gradient-start" size={24} />
        </div>
        <div>
            <h1 className="text-2xl font-bold text-text-primary">{t('settings.trainer.title')}</h1>
            <p className="text-text-secondary mt-3">{t('settings.trainer.subtitle')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {availableTrainers.map((t_data) => {
          const trainerId = t_data.trainer_id.toLowerCase();
          const isLocked = isFreePlan && trainerId !== 'gymbro';

          return (
            <div
              key={t_data.trainer_id}
              onClick={() => { 
                if (isLocked) {
                  window.location.hash = 'plans';
                  return;
                }
                setSelectedTrainerId(t_data.trainer_id); 
              }}
              className={cn(
                "relative cursor-pointer rounded-xl border-2 p-6 transition-all duration-300 hover:scale-[1.02]",
                selectedTrainerId === t_data.trainer_id
                  ? "border-gradient-start bg-gradient-start/5 shadow-2xl shadow-primary/10"
                  : "border-white/5 bg-dark-card/50 hover:border-white/10",
                isLocked && "opacity-60 grayscale-[0.5] hover:border-red-500/30"
              )}
            >
              {isLocked && (
                <div className="absolute top-3 left-3 z-20 bg-dark-bg/80 backdrop-blur-sm p-1.5 rounded-lg border border-white/10 animate-in fade-in zoom-in duration-300">
                  <Lock size={14} className="text-gradient-start" data-testid="lock-icon" />
                </div>
              )}
              <div className={cn(
                "absolute inset-0 opacity-0 transition-opacity duration-300 rounded-xl bg-gradient-to-br",
                getTrainerColor(trainerId),
                selectedTrainerId === t_data.trainer_id ? "opacity-5" : "group-hover:opacity-5"
              )} />
              
              <div className="flex items-start justify-between relative z-10">
                <div className="flex items-center gap-5">
                   <div className={cn(
                     "w-20 h-20 rounded-2xl p-0.5 bg-gradient-to-br shadow-inner shrink-0 overflow-hidden",
                     getTrainerColor(trainerId)
                   )}>
                      <img 
                        src={`/assets/avatars/${trainerId}.png`}
                        alt={t_data.name}
                        className="w-full h-full object-cover rounded-[14px]"
                        onError={(e) => {
                          // Fallback to initial if image fails
                          e.currentTarget.style.display = 'none';
                          e.currentTarget.parentElement?.classList.add('flex', 'items-center', 'justify-center');
                          const span = document.createElement('span');
                          span.textContent = t_data.name[0] ?? '';
                          span.className = "text-white font-bold text-2xl";
                          e.currentTarget.parentElement?.appendChild(span);
                        }}
                      />
                   </div>
                   <div>
                     <h3 className="font-bold text-white text-xl">{t_data.name}</h3>
                     <p className="text-text-secondary text-sm mt-1 leading-relaxed">
                       {t(`landing.trainers.profiles.${trainerId}.tagline`, { defaultValue: t_data.short_description })}
                     </p>
                   </div>
                </div>
                
                <div className={cn(
                  "w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors",
                  selectedTrainerId === t_data.trainer_id
                    ? "border-gradient-start bg-gradient-start text-black"
                    : "border-text-tertiary"
                )}>
                  {selectedTrainerId === t_data.trainer_id && <Check size={14} strokeWidth={3} />}
                </div>
              </div>
              
              <div className="mt-4 pt-4 border-t border-white/5">
                  <p className="text-xs text-text-muted italic">
                    "{t(`landing.trainers.profiles.${trainerId}.catchphrase`, { defaultValue: t_data.catchphrase })}"
                  </p>
              </div>
            </div>
          );
        })}
      </div>
      
      {availableTrainers.length === 0 && !isLoading && (
        <div className="text-center p-8 bg-dark-card border border-white/5 rounded-xl">
             <AlertCircle className="mx-auto text-red-400 mb-2" size={32} />
             <p className="text-text-secondary">{t('settings.trainer.load_error')}</p>
             <Button variant="ghost" onClick={() => { void fetchAvailableTrainers(); }} className="mt-4">
                 {t('settings.trainer.retry')}
             </Button>
        </div>
      )}

      <div className="flex justify-end pt-6 border-t border-border">
          <Button 
            onClick={() => { void handleSave(); }} 
            disabled={isSaving || !selectedTrainerId} 
            size="lg"
            className="w-full md:w-auto"
          >
             {isSaving ? t('settings.trainer.saving') : t('settings.trainer.save_button')}
          </Button>
      </div>
    </div>
  );
}

