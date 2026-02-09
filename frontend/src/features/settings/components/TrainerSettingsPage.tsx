import { Check, Dumbbell, AlertCircle } from 'lucide-react';
import { useState, useEffect } from 'react';

import { Button } from '../../../shared/components/ui/Button';
import { Skeleton } from '../../../shared/components/ui/Skeleton';
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
  const [selectedTrainerId, setSelectedTrainerId] = useState<string>('');

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
      notify.success('Treinador atualizado com sucesso!');
    } catch {
      notify.error('Erro ao atualizar treinador');
    }
  };

  const getTrainerColor = (id: string) => TRAINER_COLORS[id] ?? 'from-gray-500 to-gray-700';

  if (isLoading && availableTrainers.length === 0) {
    return (
        <div className="max-w-4xl mx-auto space-y-6 p-4">
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
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-700 h-full overflow-y-auto pb-20">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-gradient-start/10 rounded-xl">
            <Dumbbell className="text-gradient-start" size={24} />
        </div>
        <div>
            <h1 className="text-2xl font-bold text-text-primary">Personal Trainer AI</h1>
            <p className="text-text-secondary">Escolha a personalidade do seu treinador virtual</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {availableTrainers.map((t) => (
          <div
            key={t.trainer_id}
            onClick={() => { setSelectedTrainerId(t.trainer_id); }}
            className={cn(
              "relative cursor-pointer rounded-xl border-2 p-6 transition-all duration-300 hover:scale-[1.02]",
              selectedTrainerId === t.trainer_id
                ? "border-gradient-start bg-gradient-start/5 shadow-2xl shadow-primary/10"
                : "border-white/5 bg-dark-card/50 hover:border-white/10"
            )}
          >
            <div className={cn(
              "absolute inset-0 opacity-0 transition-opacity duration-300 rounded-xl bg-gradient-to-br",
              getTrainerColor(t.trainer_id),
              selectedTrainerId === t.trainer_id ? "opacity-5" : "group-hover:opacity-5"
            )} />
            
            <div className="flex items-start justify-between relative z-10">
              <div className="flex items-center gap-5">
                 <div className={cn(
                   "w-20 h-20 rounded-2xl p-0.5 bg-gradient-to-br shadow-inner shrink-0 overflow-hidden",
                   getTrainerColor(t.trainer_id)
                 )}>
                    <img 
                      src={`/assets/avatars/${t.trainer_id.toLowerCase()}.png`}
                      alt={t.name}
                      className="w-full h-full object-cover rounded-[14px]"
                      onError={(e) => {
                        // Fallback to initial if image fails
                        e.currentTarget.style.display = 'none';
                        e.currentTarget.parentElement?.classList.add('flex', 'items-center', 'justify-center');
                        const span = document.createElement('span');
                        span.textContent = t.name[0] ?? '';
                        span.className = "text-white font-bold text-2xl";
                        e.currentTarget.parentElement?.appendChild(span);
                      }}
                    />
                 </div>
                 <div>
                   <h3 className="font-bold text-white text-xl">{t.name}</h3>
                   <p className="text-text-secondary text-sm mt-1 leading-relaxed">{t.short_description}</p>
                 </div>
              </div>
              
              <div className={cn(
                "w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors",
                selectedTrainerId === t.trainer_id
                  ? "border-gradient-start bg-gradient-start text-black"
                  : "border-text-tertiary"
              )}>
                {selectedTrainerId === t.trainer_id && <Check size={14} strokeWidth={3} />}
              </div>
            </div>
            
            {t.catchphrase && (
                <div className="mt-4 pt-4 border-t border-white/5">
                    <p className="text-xs text-text-muted italic">"{t.catchphrase}"</p>
                </div>
            )}
          </div>
        ))}
      </div>
      
      {availableTrainers.length === 0 && !isLoading && (
        <div className="text-center p-8 bg-dark-card border border-white/5 rounded-xl">
             <AlertCircle className="mx-auto text-red-400 mb-2" size={32} />
             <p className="text-text-secondary">Não foi possível carregar os treinadores disponíveis.</p>
             <Button variant="ghost" onClick={() => { void fetchAvailableTrainers(); }} className="mt-4">
                 Tentar Novamente
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
             {isSaving ? 'Salvando...' : 'Atualizar Treinador'}
          </Button>
      </div>
    </div>
  );
}
