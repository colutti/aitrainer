import { zodResolver } from '@hookform/resolvers/zod';
import { User, Save } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { Button } from '../../../shared/components/ui/Button';
import { Input } from '../../../shared/components/ui/Input';
import { useAuthStore } from '../../../shared/hooks/useAuth';
import { useNotificationStore } from '../../../shared/hooks/useNotification';
import { settingsApi } from '../api/settings-api';

import { PhotoUpload } from './PhotoUpload';

const profileSchema = z.object({
  display_name: z.string().max(50).optional(),
  email: z.string().email(),
  age: z.coerce.number().min(1, 'Idade inválida'),
  weight: z.coerce.number().min(1, 'Peso inválido'),
  height: z.coerce.number().min(1, 'Altura inválida'),
  gender: z.string().min(1, 'Gênero obrigatório'),
  goal: z.string().optional(),
  goal_type: z.enum(['lose', 'gain', 'maintain']),
  weekly_rate: z.coerce.number(),
  target_weight: z.coerce.number().optional()
});

type ProfileForm = z.infer<typeof profileSchema>;

export function UserProfilePage() {
  const notify = useNotificationStore();
  const { userInfo, loadUserInfo } = useAuthStore();
  const [photo, setPhoto] = useState<string | null | undefined>(userInfo?.photo_base64);
  const [isSaving, setIsSaving] = useState(false);

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema)
  });

  useEffect(() => {
    async function load() {
      try {
        const data = await settingsApi.getProfile();
        // Default values for missing fields to avoid uncontrolled input warnings
        reset({
          ...data,
          goal: data.goal ?? '',
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

      notify.success('Perfil atualizado com sucesso!');
    } catch {
      notify.error('Erro ao atualizar perfil');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-700 h-full overflow-y-auto pb-20">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-gradient-start/10 rounded-xl">
            <User className="text-gradient-start" size={24} />
        </div>
        <div>
            <h1 className="text-2xl font-bold text-text-primary">Perfil do Usuário</h1>
            <p className="text-text-secondary">Gerencie suas informações pessoais e objetivos</p>
        </div>
      </div>

      <form onSubmit={(e) => {
        void handleSubmit(onSubmit)(e);
      }} className="space-y-6 bg-dark-card p-6 rounded-xl border border-border shadow-sm">
        {/* Identity Section */}
        <div className="border-b border-border pb-6">
          <h3 className="text-lg font-semibold text-text-primary mb-4">Identidade</h3>
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
              label="Nome Exibido"
              placeholder="Seu nome para o app e treinador"
              maxLength={50}
              {...register('display_name')}
              error={errors.display_name?.message}
            />
          </div>
        </div>

        <Input id="profile-email" label="Email" {...register('email')} disabled className="opacity-60 cursor-not-allowed" />
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input id="profile-age" label="Idade" type="number" {...register('age')} error={errors.age?.message} />
            <Input id="profile-gender" label="Gênero" {...register('gender')} error={errors.gender?.message} />
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input id="profile-weight" label="Peso (kg)" type="number" step="0.1" {...register('weight')} error={errors.weight?.message} />
            <Input id="profile-height" label="Altura (cm)" type="number" {...register('height')} error={errors.height?.message} />
        </div>

        <div className="border-t border-border pt-4 mt-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Metas & Objetivos</h3>
            
             <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                    <label className="text-sm font-medium text-text-secondary px-1 block mb-1.5">Tipo de Objetivo</label>
                    <select
                    {...register('goal_type')}
                    className="flex h-11 w-full rounded-lg bg-dark-card border border-border px-3 py-2 text-sm transition-all focus:outline-none focus:ring-2 focus:ring-gradient-start/20 focus:border-gradient-start text-white"
                    >
                        <option value="lose">Perder Peso</option>
                        <option value="gain">Ganhar Massa</option>
                        <option value="maintain">Manter Peso</option>
                    </select>
                </div>
                 <Input id="profile-weekly-rate" label="Meta Semanal (kg)" type="number" step="0.1" {...register('weekly_rate')} error={errors.weekly_rate?.message} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input label="Peso Alvo (kg)" type="number" step="0.1" {...register('target_weight')} error={errors.target_weight?.message} />
                <Input label="Descrição do Objetivo" {...register('goal')} error={errors.goal?.message} placeholder="Ex: Ficar mais definido para o verão" />
            </div>
        </div>

        <div className="flex justify-end pt-6">
            <Button type="submit" disabled={isSubmitting || isSaving} className="w-full md:w-auto">
                <Save className="mr-2 h-4 w-4" /> {isSaving ? 'Salvando...' : 'Salvar Alterações'}
            </Button>
        </div>
      </form>
    </div>
  );
}
