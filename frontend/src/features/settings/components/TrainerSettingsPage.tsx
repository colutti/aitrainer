import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import { useAuthStore } from '../../../shared/hooks/useAuth';
import { useNotificationStore } from '../../../shared/hooks/useNotification';
import { useSettingsStore } from '../../../shared/hooks/useSettings';

import { TrainerSettingsView } from './TrainerSettingsView';

/**
 * TrainerSettingsPage component (Container)
 * 
 * Manages the selection and persistence of the user's AI trainer.
 * Delegates rendering to TrainerSettingsView.
 */
export default function TrainerSettingsPage() {
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

  useEffect(() => {
    void fetchAvailableTrainers();
    void fetchTrainer();
  }, [fetchAvailableTrainers, fetchTrainer]);

  // Use a separate effect to sync the ID from the store to the local state
  // to avoid blocking the initial render or return-type issues
  useEffect(() => {
    if (trainer?.trainer_type && !selectedTrainerId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSelectedTrainerId(trainer.trainer_type);
    }
  }, [trainer, selectedTrainerId]);

  const handleSelect = (id: string) => {
    const isFreePlan = userInfo?.subscription_plan === 'Free' || userInfo?.subscription_plan === 'FREE';
    const trainerId = id.toLowerCase();
    const isLocked = isFreePlan && trainerId !== 'gymbro';
    
    if (isLocked) {
      window.location.href = '/dashboard/settings/subscription';
      return;
    }
    
    setSelectedTrainerId(id);
  };

  const onSave = () => {
    const runSave = async () => {
      if (!selectedTrainerId) return;
      try {
        await updateTrainer(selectedTrainerId);
        notify.success(t('settings.trainer.update_success'));
      } catch {
        notify.error(t('settings.trainer.update_error'));
      }
    };
    void runSave();
  };

  return (
    <TrainerSettingsView 
      availableTrainers={availableTrainers}
      selectedTrainerId={selectedTrainerId}
      isSaving={isSaving}
      isLoading={isLoading}
      isFreePlan={userInfo?.subscription_plan === 'Free' || userInfo?.subscription_plan === 'FREE'}
      onSelect={handleSelect}
      onSave={onSave}
      onRetry={() => { void fetchAvailableTrainers(); }}
    />
  );
}
