import { zodResolver } from '@hookform/resolvers/zod';
import { Camera, Mail, Activity, Target, ChevronRight, User, Ruler, TrendingUp } from 'lucide-react';
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
  onSubmit: (data: UserProfileForm) => Promise<void>;
  onPhotoUpload: (file: File) => Promise<void>;
}

export default function UserProfileView({
  profile,
  isLoading,
  isSaving,
  photoBase64,
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
        target_weight: profile.target_weight ?? undefined,
        goal_type: profile.goal_type,
        weekly_rate: profile.weekly_rate,
      });
    }
  }, [profile, reset]);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-pulse">
        <div className="lg:col-span-1 space-y-6">
          <div className="h-80 bg-white/5 rounded-[32px]" />
        </div>
        <div className="lg:col-span-2 space-y-6">
          <div className="h-96 bg-white/5 rounded-[32px]" />
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
           <div className="relative group cursor-pointer" onClick={() => document.getElementById('photo-upload')?.click()}>
              <div className="w-32 h-32 rounded-[40px] bg-zinc-800 border-4 border-white/10 overflow-hidden shadow-2xl transition-transform group-hover:scale-105">
                 {photoUrl ? (
                   <img src={photoUrl} alt="Profile" className="w-full h-full object-cover" />
                 ) : (
                   <div className="w-full h-full flex items-center justify-center bg-indigo-500/20 text-indigo-400">
                      <User size={48} />
                   </div>
                 )}
              </div>

              <input 
                id="photo-upload"
                type="file" 
                className="hidden" 
                accept="image/*"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) void onPhotoUpload(file);
                }}
              />
              <div className="absolute -bottom-2 -right-2 w-10 h-10 rounded-full bg-indigo-500 border-4 border-[#09090b] flex items-center justify-center text-white shadow-lg">
                 <Camera size={16} />
              </div>
           </div>

           <div className="mt-6 mb-8">
              <h2 data-testid="profile-header-name" className="text-xl font-black text-white leading-tight">{userName}</h2>
              <p className="text-sm text-zinc-500 font-medium flex items-center justify-center gap-2 mt-1">
                <Mail size={14} /> {profile?.email}
              </p>
           </div>

           <div className="grid grid-cols-2 gap-4 w-full">
              <div className="bg-white/5 p-3 rounded-2xl border border-white/5">
                <p className="text-[9px] uppercase font-black text-zinc-600 tracking-widest">{t('common.age')}</p>
                <p className="text-lg font-black text-white">{profile?.age ?? '-'}</p>
              </div>
              <div className="bg-white/5 p-3 rounded-2xl border border-white/5">
                <p className="text-[9px] uppercase font-black text-zinc-600 tracking-widest">{t('common.gender')}</p>
                <p className="text-lg font-black text-white capitalize">{profile?.gender ?? '-'}</p>
              </div>
           </div>
        </PremiumCard>
      </div>

      {/* DETAILED FORM */}
      <div className="lg:col-span-2 space-y-6">
        <PremiumCard className="p-8">
           <div className="flex items-center gap-3 mb-8">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                 <Activity size={20} />
              </div>
              <h3 className="text-xl font-black text-white tracking-tight uppercase">{t('settings.profile.personal_info')}</h3>
           </div>

           <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <FormField label={t('settings.profile.name')} id="profile-name" icon={<User size={18} />} error={errors.display_name?.message}>
                <Input 
                  id="profile-name" 
                  data-testid="profile-name"
                  {...register('display_name')} 
                  className="pl-12 h-14 bg-white/5 border-white/5 rounded-2xl focus:border-white/20 text-white"
                />
              </FormField>

              <FormField label={t('common.gender')} id="profile-gender" icon={<User size={18} />} error={errors.gender?.message}>
                <select 
                  id="profile-gender"
                  {...register('gender')}
                  className="flex h-14 w-full rounded-2xl bg-white/5 border border-white/5 px-4 py-2 text-sm text-white transition-all focus:outline-none focus:border-white/20"
                >
                  <option value="male">{t('onboarding.genders.male')}</option>
                  <option value="female">{t('onboarding.genders.female')}</option>
                </select>
              </FormField>

              <FormField label={t('common.age')} id="profile-age" icon={<Activity size={18} />} error={errors.age?.message}>
                <Input 
                  id="profile-age"
                  data-testid="profile-age"
                  type="number"
                  {...register('age', { valueAsNumber: true })}
                  className="pl-12 h-14 bg-white/5 border-white/5 rounded-2xl focus:border-white/20 text-white"
                />
              </FormField>

              <FormField label={t('settings.height')} id="profile-height" icon={<Ruler size={18} />} error={errors.height?.message}>
                <div className="relative">
                  <Input 
                    id="profile-height"
                    data-testid="profile-height"
                    type="number"
                    {...register('height', { valueAsNumber: true })}
                    className="pl-12 h-14 bg-white/5 border-white/5 rounded-2xl focus:border-white/20 text-white"
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-bold text-zinc-500 uppercase tracking-widest">cm</span>
                </div>
              </FormField>
           </div>
        </PremiumCard>

        <PremiumCard className="p-8">
           <div className="flex items-center gap-3 mb-8">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                 <Target size={20} />
              </div>
              <h3 className="text-xl font-black text-white tracking-tight uppercase">{t('settings.profile.goals')}</h3>
           </div>

           <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <FormField label={t('settings.profile.goal_type')} id="profile-goal" icon={<Target size={18} />}>
                <select 
                  id="profile-goal"
                  {...register('goal_type')}
                  className="flex h-14 w-full rounded-2xl bg-white/5 border border-white/5 px-4 py-2 text-sm text-white transition-all focus:outline-none focus:border-white/20"
                >
                  <option value="lose">{t('onboarding.goals.lose')}</option>
                  <option value="maintain">{t('onboarding.goals.maintain')}</option>
                  <option value="gain">{t('onboarding.goals.gain')}</option>
                </select>
              </FormField>

              <FormField label={t('settings.profile.target_weight')} id="profile-target" icon={<Ruler size={18} />} error={errors.target_weight?.message}>
                <div className="relative">
                  <Input 
                    id="profile-target"
                    data-testid="profile-target"
                    type="number"
                    {...register('target_weight', { valueAsNumber: true })}
                    className="pl-12 h-14 bg-white/5 border-white/5 rounded-2xl focus:border-white/20 text-white"
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-bold text-zinc-500 uppercase tracking-widest">kg</span>
                </div>
              </FormField>

              <FormField label={t('settings.profile.weekly_rate')} id="profile-weekly-rate" icon={<TrendingUp size={18} />} error={errors.weekly_rate?.message}>
                <div className="relative">
                  <Input 
                    id="profile-weekly-rate"
                    data-testid="profile-weekly-rate"
                    type="number"
                    step="0.1"
                    {...register('weekly_rate', { valueAsNumber: true })}
                    className="pl-12 h-14 bg-white/5 border-white/5 rounded-2xl focus:border-white/20 text-white"
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-bold text-zinc-500 uppercase tracking-widest">kg/sem</span>
                </div>
              </FormField>
           </div>

           <div className="mt-10 flex justify-end">
              <Button 
                type="submit" 
                disabled={isSaving}
                className="btn-premium h-14 px-10 rounded-2xl text-base shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all"
              >
                {isSaving ? t('common.loading') : t('common.save')}
                <ChevronRight className="ml-2 w-5 h-5" />
              </Button>
           </div>
        </PremiumCard>
      </div>
    </form>
  );
}
