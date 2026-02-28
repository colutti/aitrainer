import { zodResolver } from '@hookform/resolvers/zod';
import { User, Save, Globe } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { z } from 'zod';

import { Button } from '../../../shared/components/ui/Button';
import { Input } from '../../../shared/components/ui/Input';
import { useAuthStore } from '../../../shared/hooks/useAuth';
import { useNotificationStore } from '../../../shared/hooks/useNotification';
import { cn } from '../../../shared/utils/cn';
import { settingsApi } from '../api/settings-api';

import { PhotoUpload } from './PhotoUpload';



export function UserProfilePage() {
  const notify = useNotificationStore();
  const { userInfo, loadUserInfo } = useAuthStore();
  const { t, i18n } = useTranslation();

  const profileSchema = z.object({
    display_name: z.string().max(50).optional(),
    email: z.string().email(),
    age: z.coerce.number().min(1, { message: t('validation.invalid_age') }),
    height: z.coerce.number().min(1),
    gender: z.string().min(1),
    goal_type: z.enum(['lose', 'gain', 'maintain']),
    weekly_rate: z.coerce.number(),
    target_weight: z.preprocess(
      (val) => (val === '' || val === null || val === undefined) ? undefined : Number(val),
      z.number().positive().optional()
    )
  });

  type ProfileForm = z.infer<typeof profileSchema>;

  const WEEKLY_RATE_OPTIONS = [
    { value: 0.25, label: `0.25 ${t('settings.kg_week')}` },
    { value: 0.5,  label: `0.5 ${t('settings.kg_week')} (${t('settings.recommended')})` },
    { value: 0.75, label: `0.75 ${t('settings.kg_week')}` },
    { value: 1,    label: `1.0 ${t('settings.kg_week')}` },
    { value: 1.5,  label: `1.5 ${t('settings.kg_week')}` },
    { value: 2,    label: `2.0 ${t('settings.kg_week')} (${t('settings.maximum')})` },
  ] as const;

  const [photo, setPhoto] = useState<string | null | undefined>(userInfo?.photo_base64);
  const [isSaving, setIsSaving] = useState(false);

  const { register, handleSubmit, reset, watch, setValue, formState: { errors, isSubmitting } } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema)
  });

  const goalType = watch('goal_type');

  useEffect(() => {
    if (goalType === 'maintain') {
      setValue('weekly_rate', 0);
    } else {
      const currentRate = watch('weekly_rate');
      if (!currentRate || currentRate === 0) {
        setValue('weekly_rate', 0.5);
      }
    }
  }, [goalType, setValue, watch]);

  useEffect(() => {
    async function load() {
      try {
        const data = await settingsApi.getProfile();
        // Default values for missing fields to avoid uncontrolled input warnings
        reset({
          ...data,
          target_weight: data.target_weight ?? undefined,
          weekly_rate: data.weekly_rate,
          display_name: typeof data.display_name === 'string' ? data.display_name : ''
        } satisfies ProfileForm);
        setPhoto(data.photo_base64);
      } catch {
        // Silently fail - user will see empty form
      }
    }
    void load();
  }, [reset]);

  const onSubmit = async (data: ProfileForm) => {
    setIsSaving(true);
    try {
      // Update identity (name + photo) in parallel with profile
      const identityUpdate: { display_name?: string | null; photo_base64?: string | null } = {
        display_name: data.display_name ?? undefined,
        photo_base64: photo === undefined ? undefined : photo
      };

      await Promise.all([
        settingsApi.updateProfile(data),
        settingsApi.updateIdentity(identityUpdate)
      ]);

      // Refresh auth store to update sidebar/dashboard with new name/photo
      await loadUserInfo();

      notify.success(t('settings.update_success'));
    } catch {
      notify.error(t('settings.update_error'));
    } finally {
      setIsSaving(false);
    }
  };

  const changeLanguage = (lng: string) => {
    void i18n.changeLanguage(lng);
  };

  const isMaintain = goalType === 'maintain';

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-700 h-full overflow-y-auto pb-20">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-gradient-start/10 rounded-xl">
            <User className="text-gradient-start" size={24} />
        </div>
        <div>
            <h1 className="text-2xl font-bold text-text-primary">{t('settings.profile_title')}</h1>
            <p className="text-text-secondary">{t('settings.profile_subtitle')}</p>
        </div>
      </div>

      <div className="space-y-6 bg-dark-card p-6 rounded-xl border border-border shadow-sm">
        {/* Identity Section */}
        <form onSubmit={(e) => {
          void handleSubmit(onSubmit)(e);
        }} className="space-y-6">
          <div className="border-b border-border pb-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">{t('settings.identity')}</h3>
            <div className="space-y-4">
              <PhotoUpload
                currentPhoto={photo}
                displayName={userInfo?.name}
                email={userInfo?.email ?? 'user@example.com'}
                onPhotoChange={(newPhoto) => {
                  setPhoto(newPhoto);
                }}
                isLoading={isSaving}
              />
              <Input
                id="profile-display-name"
                label={t('settings.display_name')}
                placeholder={t('settings.display_name_placeholder')}
                maxLength={50}
                {...register('display_name')}
                error={errors.display_name?.message}
              />
            </div>
          </div>

          <Input id="profile-email" label={t('settings.email')} {...register('email')} disabled className="opacity-60 cursor-not-allowed" />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input id="profile-age" label={t('settings.age')} type="number" {...register('age')} error={errors.age?.message} />
              <Input id="profile-gender" label={t('settings.gender')} {...register('gender')} error={errors.gender?.message} />
          </div>

          <Input id="profile-height" label={t('settings.height')} type="number" {...register('height')} error={errors.height?.message} />

          <div className="border-t border-border pt-4 mt-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4">{t('settings.goals_title')}</h3>

               <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                      <label htmlFor="profile-goal-type" className="text-sm font-medium text-text-secondary px-1 block mb-1.5">{t('settings.goal_type')}</label>
                      <select
                        id="profile-goal-type"
                        {...register('goal_type')}
                        className="flex h-11 w-full rounded-lg bg-dark-card border border-border px-3 py-2 text-sm transition-all focus:outline-none focus:ring-2 focus:ring-gradient-start/20 focus:border-gradient-start text-white"
                      >
                          <option value="lose">{t('settings.goal_lose')}</option>
                          <option value="gain">{t('settings.goal_gain')}</option>
                          <option value="maintain">{t('settings.goal_maintain')}</option>
                      </select>
                  </div>

                  <div>
                      <label htmlFor="profile-weekly-rate" className="text-sm font-medium text-text-secondary px-1 block mb-1.5">{t('settings.weekly_rate')}</label>
                      <select
                        id="profile-weekly-rate"
                        {...register('weekly_rate')}
                        disabled={isMaintain}
                        className="flex h-11 w-full rounded-lg bg-dark-card border border-border px-3 py-2 text-sm transition-all focus:outline-none focus:ring-2 focus:ring-gradient-start/20 focus:border-gradient-start text-white disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {WEEKLY_RATE_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                      {errors.weekly_rate && (
                        <p className="text-red-400 text-xs mt-1 px-1">{errors.weekly_rate.message}</p>
                      )}
                  </div>
              </div>

              <Input id="profile-target-weight" label={t('settings.target_weight')} type="number" step="0.1" {...register('target_weight')} error={errors.target_weight?.message} />
          </div>

          <div className="flex justify-end pt-6">
              <Button type="submit" disabled={isSubmitting || isSaving} className="w-full md:w-auto">
                  <Save className="mr-2 h-4 w-4" /> {isSaving ? t('settings.saving') : t('settings.save_changes')}
              </Button>
          </div>
        </form>

        {/* Language Section */}
        <div className="border-t border-border pt-6 mt-6">
          <div className="flex items-center gap-2 mb-4">
             <Globe className="text-gradient-start" size={20} />
             <h3 className="text-lg font-semibold text-text-primary">{t('settings.language')}</h3>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
             <button
               onClick={() => { changeLanguage('pt-BR'); }}
               className={cn(
                 "p-4 rounded-xl border text-sm font-medium transition-all text-center",
                 i18n.language === 'pt-BR' 
                  ? "bg-gradient-start/10 border-gradient-start text-gradient-start" 
                  : "bg-dark-bg border-border text-text-secondary hover:border-white/20"
               )}
             >
               {t('settings.language_pt')}
             </button>
             <button
               onClick={() => { changeLanguage('es-ES'); }}
               className={cn(
                 "p-4 rounded-xl border text-sm font-medium transition-all text-center",
                 i18n.language === 'es-ES' 
                  ? "bg-gradient-start/10 border-gradient-start text-gradient-start" 
                  : "bg-dark-bg border-border text-text-secondary hover:border-white/20"
               )}
             >
               {t('settings.language_es')}
             </button>
             <button
               onClick={() => { changeLanguage('en-US'); }}
               className={cn(
                 "p-4 rounded-xl border text-sm font-medium transition-all text-center",
                 i18n.language === 'en-US' 
                  ? "bg-gradient-start/10 border-gradient-start text-gradient-start" 
                  : "bg-dark-bg border-border text-text-secondary hover:border-white/20"
               )}
             >
               {t('settings.language_en')}
             </button>
          </div>
        </div>
      </div>
    </div>
  );
}
