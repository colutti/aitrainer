import { zodResolver } from '@hookform/resolvers/zod';
import { Camera, Mail, Activity, ChevronRight, User, Ruler } from 'lucide-react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { Input } from '../../../shared/components/ui/Input';
import { FormField } from '../../../shared/components/ui/premium/FormField';
import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { type UserProfile as UserInfo } from '../../../shared/types/user-profile';
import { userProfileSchema, type UserProfileForm } from '../schemas/user-profile-schema';

interface UserProfileViewProps {
  profile: UserInfo | null;
  isLoading: boolean;
  isSaving: boolean;
  photoBase64: string | null;
  isReadOnly?: boolean;
  onSubmit: (data: UserProfileForm) => Promise<void>;
  onPhotoUpload: (file: File) => Promise<void>;
}

export default function UserProfileView({
  profile,
  isLoading,
  isSaving,
  photoBase64,
  isReadOnly = false,
  onSubmit,
  onPhotoUpload,
}: UserProfileViewProps) {
  const { t } = useTranslation();
  const { register, handleSubmit, reset, formState: { errors } } = useForm<UserProfileForm>({
    resolver: zodResolver(userProfileSchema),
  });

  useEffect(() => {
    if (profile) {
      reset({
        display_name: profile.display_name,
        gender: profile.gender,
        age: profile.age,
        height: profile.height,
      });
    }
  }, [profile, reset]);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-pulse">
        <div className="lg:col-span-1 space-y-6">
          <div className="h-80 bg-[color:var(--color-surface-container)] rounded-[var(--radius-lg)]" />
        </div>
        <div className="lg:col-span-2 space-y-6">
          <div className="h-96 bg-[color:var(--color-surface-container)] rounded-[var(--radius-lg)]" />
        </div>
      </div>
    );
  }

  const userName = profile?.display_name ?? t('common.athlete');

  const photoUrl = photoBase64 ?? profile?.photo_base64;

  return (
    <form onSubmit={(e) => { void handleSubmit(onSubmit)(e); }} data-testid="profile-form" className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* SIDEBAR: PHOTO & QUICK STATS */}
      <div className="lg:col-span-1 space-y-6">
        <PremiumCard className="p-8 text-center flex flex-col items-center">
           <div className={`relative group ${isReadOnly ? 'cursor-default' : 'cursor-pointer'}`} onClick={() => { if (!isReadOnly) document.getElementById('photo-upload')?.click(); }}>
              <div className="w-32 h-32 rounded-[40px] bg-[color:var(--color-surface-container)] border-4 border-[color:var(--color-outline-variant)] overflow-hidden  transition-transform group-hover:scale-105">
                 {photoUrl ? (
                   <img src={photoUrl} alt="Profile" className="w-full h-full object-cover" />
                 ) : (
                   <div className="w-full h-full flex items-center justify-center bg-indigo-500/20 text-[color:var(--color-primary)]">
                      <User size={48} />
                   </div>
                 )}
              </div>

              <input 
                id="photo-upload"
                type="file" 
                className="hidden" 
                accept="image/*"
                disabled={isReadOnly}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) void onPhotoUpload(file);
                }}
              />
              <div className="absolute -bottom-2 -right-2 w-10 h-10 rounded-full bg-indigo-500 border-4 border-[#09090b] flex items-center justify-center text-text-primary ">
                 <Camera size={16} />
              </div>
           </div>
           {isReadOnly && (
             <div className="mt-4 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-[10px] font-semibold uppercase tracking-[0.2em] text-amber-300">
               Demo Read-Only
             </div>
           )}

           <div className="mt-6 mb-8">
              <h2 data-testid="profile-header-name" className="text-xl font-semibold text-text-primary leading-tight">{userName}</h2>
              <p className="text-sm text-text-muted font-medium flex items-center justify-center gap-2 mt-1">
                <Mail size={14} /> {profile?.email}
              </p>
           </div>

           <div className="grid grid-cols-2 gap-4 w-full">
              <div className="bg-[color:var(--color-surface-container)] p-3 rounded-2xl border border-[color:var(--color-outline-variant)]">
                <p className="text-[9px] uppercase font-semibold text-text-muted tracking-[0.05em]">{t('common.age')}</p>
                <p className="text-lg font-semibold text-text-primary">{profile?.age ?? '-'}</p>
              </div>
              <div className="bg-[color:var(--color-surface-container)] p-3 rounded-2xl border border-[color:var(--color-outline-variant)]">
                <p className="text-[9px] uppercase font-semibold text-text-muted tracking-[0.05em]">{t('common.gender')}</p>
                <p className="text-lg font-semibold text-text-primary capitalize">{profile?.gender ?? '-'}</p>
              </div>
           </div>
        </PremiumCard>
      </div>

      {/* DETAILED FORM */}
      <div className="lg:col-span-2 space-y-6">
        <PremiumCard className="p-8">
           <div className="flex items-center gap-3 mb-8">
              <div className="w-10 h-10 rounded-xl bg-[color:var(--color-primary)]/10 border border-[color:var(--color-primary)]/20 flex items-center justify-center text-[color:var(--color-primary)]">
                 <Activity size={20} />
              </div>
              <h3 className="text-xl font-semibold text-text-primary tracking-tight uppercase">{t('settings.profile.personal_info')}</h3>
           </div>

           <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <FormField label={t('settings.profile.name')} id="profile-name" icon={<User size={18} />} error={errors.display_name?.message}>
                  <Input 
                    id="profile-name" 
                    data-testid="profile-name"
                    disabled={isReadOnly}
                    {...register('display_name')} 
                  className="pl-12 h-14 rounded-2xl"
                />
              </FormField>

              <FormField label={t('common.gender')} id="profile-gender" icon={<User size={18} />} error={errors.gender?.message}>
                  <select 
                    id="profile-gender"
                    disabled={isReadOnly}
                    {...register('gender')}
                  className="form-field flex h-14 w-full rounded-2xl px-4 py-2 text-sm"
                >
                  <option value={t('onboarding.genders.male')}>{t('onboarding.genders.male')}</option>
                  <option value={t('onboarding.genders.female')}>{t('onboarding.genders.female')}</option>
                </select>
              </FormField>

              <FormField label={t('common.age')} id="profile-age" icon={<Activity size={18} />} error={errors.age?.message}>
                  <Input 
                    id="profile-age"
                    data-testid="profile-age"
                    type="number"
                    step="any"
                    disabled={isReadOnly}
                    {...register('age', { valueAsNumber: true })}
                  className="pl-12 h-14 rounded-2xl"
                />
              </FormField>

              <FormField label={t('settings.height')} id="profile-height" icon={<Ruler size={18} />} error={errors.height?.message}>
                <div className="relative">
                  <Input 
                    id="profile-height"
                    data-testid="profile-height"
                    type="number"
                    step="any"
                    disabled={isReadOnly}
                    {...register('height', { valueAsNumber: true })}
                    className="pl-12 h-14 rounded-2xl"
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-bold text-text-muted uppercase tracking-[0.05em]">cm</span>
                </div>
              </FormField>
           </div>
        </PremiumCard>

        <div className="mt-2 flex justify-end">
          <Button
            type="submit"
            disabled={isSaving || isReadOnly}
            className="btn-premium h-14 px-10 rounded-2xl text-base  hover:scale-[1.02] active:scale-[0.98] transition-all"
          >
            {isReadOnly ? t('settings.profile.read_only', 'Somente leitura') : isSaving ? t('common.loading') : t('common.save')}
            <ChevronRight className="ml-2 w-5 h-5" />
          </Button>
        </div>
      </div>
    </form>
  );
}
