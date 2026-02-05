import { 
  User, 
  Settings as SettingsIcon, 
  LogOut, 
  ChevronRight, 
  Shield, 
  Database, 
  Bell,
  Heart,
  Target,
  Dumbbell
} from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '../../shared/components/ui/Button';
import { Input } from '../../shared/components/ui/Input';
import { useAuthStore } from '../../shared/hooks/useAuth';
import { useConfirmation } from '../../shared/hooks/useConfirmation';
import { useNotificationStore } from '../../shared/hooks/useNotification';
import { useSettingsStore } from '../../shared/hooks/useSettings';
import { UserProfile } from '../../shared/types/settings';
import { cn } from '../../shared/utils/cn';

/**
 * SettingsPage component
 * 
 * Manage user profile, goals, trainer preferences and account security.
 */
export function SettingsPage() {
  const { 
    profile, 
    trainer, 
    availableTrainers,
    isLoading, 
    isSaving,
    fetchProfile, 
    updateProfile, 
    fetchTrainer, 
    fetchAvailableTrainers, 
    updateTrainer 
  } = useSettingsStore();

  const { logout, userInfo } = useAuthStore();
  const { confirm } = useConfirmation();
  const notify = useNotificationStore();

  useEffect(() => {
    void fetchProfile();
    void fetchTrainer();
    void fetchAvailableTrainers();
  }, [fetchProfile, fetchTrainer, fetchAvailableTrainers]);

  const handleProfileSubmit = async (data: Partial<UserProfile>) => {
    try {
      await updateProfile(data);
      notify.success('Perfil atualizado com sucesso!');
    } catch {
      notify.error('Erro ao atualizar perfil.');
    }
  };

  const handleTrainerChange = async (trainerId: string) => {
    if (trainer?.trainer_type === trainerId) return;

    try {
      await updateTrainer(trainerId);
      notify.success('Treinador atualizado!');
    } catch {
      notify.error('Erro ao mudar treinador.');
    }
  };

  const handleLogout = async () => {
    const isConfirmed = await confirm({
      title: 'Sair da Conta',
      message: 'Deseja realmente encerrar sua sessão?',
      confirmText: 'Sair',
      type: 'danger'
    });

    if (isConfirmed) {
      logout();
    }
  };

  if (isLoading && !profile) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <div className="w-12 h-12 border-4 border-gradient-start border-t-transparent rounded-full animate-spin" />
        <p className="mt-4 text-text-secondary animate-pulse">Carregando suas configurações...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-20">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
            <SettingsIcon className="text-gradient-start" size={32} />
            Configurações
          </h1>
          <p className="text-text-secondary mt-1">Gerencie seu perfil e preferências do app.</p>
        </div>
        <Button 
          variant="danger" 
          size="lg" 
          onClick={() => {
            void handleLogout();
          }} 
          className="gap-2"
        >
          <LogOut size={20} />
          Sair
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Navigation Sidebar */}
        <div className="md:col-span-1 space-y-2">
          <nav className="space-y-1">
            <button className="w-full flex items-center justify-between p-3 rounded-xl bg-gradient-start/10 text-gradient-start font-bold">
              <div className="flex items-center gap-3">
                <User size={20} />
                Perfil Pessoal
              </div>
              <ChevronRight size={16} />
            </button>
            <button className="w-full flex items-center justify-between p-3 rounded-xl text-text-secondary hover:bg-dark-card transition-colors">
              <div className="flex items-center gap-3">
                <Target size={20} />
                Treinador AI
              </div>
              <ChevronRight size={16} />
            </button>
            <button className="w-full flex items-center justify-between p-3 rounded-xl text-text-secondary hover:bg-dark-card transition-colors">
              <div className="flex items-center gap-3">
                <Shield size={20} />
                Privacidade
              </div>
              <ChevronRight size={16} />
            </button>
            <button className="w-full flex items-center justify-between p-3 rounded-xl text-text-secondary hover:bg-dark-card transition-colors">
              <div className="flex items-center gap-3">
                <Database size={20} />
                Integrações
              </div>
              <ChevronRight size={16} />
            </button>
          </nav>

          <div className="pt-8 px-4">
            <div className="bg-dark-card border border-border rounded-2xl p-4 text-center">
              <div className="w-16 h-16 rounded-full bg-gradient-start mx-auto mb-3 flex items-center justify-center text-2xl font-bold text-white shadow-orange">
                {userInfo?.name.charAt(0).toUpperCase() ?? 'U'}
              </div>
              <p className="font-bold text-text-primary">{userInfo?.name ?? 'Usuário'}</p>
              <p className="text-xs text-text-muted mt-0.5">{userInfo?.email}</p>
              <div className="mt-4 pt-4 border-t border-border">
                <span className="text-[10px] uppercase font-bold text-text-muted tracking-widest">
                  Membro desde Jan 2024
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="md:col-span-2 space-y-10">
          {profile && (
            <ProfileForm 
              profile={profile} 
              onSave={handleProfileSubmit} 
              isSaving={isSaving} 
            />
          )}

          {/* Trainer Section */}
          <section className="space-y-6">
            <div className="flex items-center gap-2 pb-2 border-b border-border">
              <Dumbbell className="text-gradient-start" size={20} />
              <h2 className="text-xl font-bold text-text-primary">Personalidade do Treinador</h2>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {availableTrainers.map((t) => (
                <div 
                  key={t.id}
                  onClick={() => {
                    void handleTrainerChange(t.id);
                  }}
                  className={cn(
                    "flex items-center gap-4 p-4 rounded-2xl border transition-all cursor-pointer group",
                    trainer?.trainer_type === t.id 
                      ? "bg-gradient-start/5 border-gradient-start ring-1 ring-gradient-start shadow-orange-sm" 
                      : "bg-dark-card border-border hover:border-gradient-start/30"
                  )}
                >
                  <div className={cn(
                    "w-12 h-12 rounded-full overflow-hidden border-2 flex-shrink-0",
                    trainer?.trainer_type === t.id ? "border-gradient-start" : "border-border"
                  )}>
                    <img src={t.avatar_url} alt={t.name} className="w-full h-full object-cover" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h3 className="font-bold text-text-primary">{t.name}</h3>
                      {trainer?.trainer_type === t.id && (
                        <span className="text-[10px] font-bold bg-gradient-start text-white px-2 py-0.5 rounded-full uppercase">Ativo</span>
                      )}
                    </div>
                    <p className="text-xs text-text-secondary truncate">{t.description}</p>
                  </div>
                  <ChevronRight size={18} className={cn(
                    "text-text-muted transition-transform",
                    trainer?.trainer_type === t.id ? "translate-x-1 text-gradient-start" : "group-hover:translate-x-1"
                  )} />
                </div>
              ))}
            </div>
          </section>

          {/* Other Settings Placeholder */}
          <section className="bg-gradient-start/5 border border-gradient-start/20 rounded-2xl p-6 flex items-start gap-4">
            <Bell className="text-gradient-start mt-1" size={20} />
            <div>
              <h3 className="font-bold text-text-primary">Notificações por Email</h3>
              <p className="text-sm text-text-secondary mt-1">
                Enviaremos resumos semanais de performance e alertas para manter sua consistência. Você pode desativar isso a qualquer momento.
              </p>
              <Button variant="ghost" className="mt-4 -ml-4 text-xs font-bold text-gradient-start uppercase tracking-widest">
                Configurar Alertas
              </Button>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

interface ProfileFormProps {
  profile: NonNullable<ReturnType<typeof useSettingsStore.getState>['profile']>;
  onSave: (data: Partial<UserProfile>) => Promise<void>;
  isSaving: boolean;
}

function ProfileForm({ profile, onSave, isSaving }: ProfileFormProps) {
  const [formData, setFormData] = useState({
    age: profile.age,
    weight: profile.weight,
    height: profile.height,
    goal: profile.goal,
    goal_type: profile.goal_type,
    weekly_rate: profile.weekly_rate
  });

  return (
    <section className="space-y-6">
      <div className="flex items-center gap-2 pb-2 border-b border-border">
        <Heart className="text-gradient-start" size={20} />
        <h2 className="text-xl font-bold text-text-primary">Perfil & Métricas</h2>
      </div>

      <form 
        onSubmit={(e) => {
          e.preventDefault();
          void onSave(formData);
        }} 
        className="space-y-6"
      >
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Idade"
            type="number"
            value={formData.age}
            onChange={(e) => { setFormData({...formData, age: parseInt(e.target.value) || 0}); }}
          />
          <Input
            label="Altura (cm)"
            type="number"
            value={formData.height}
            onChange={(e) => { setFormData({...formData, height: parseInt(e.target.value) || 0}); }}
          />
          <Input
            label="Peso Atual (kg)"
            type="number"
            step="0.1"
            value={formData.weight}
            onChange={(e) => { setFormData({...formData, weight: parseFloat(e.target.value) || 0}); }}
          />
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-text-secondary uppercase tracking-wider ml-1">
              Meta Semanal (kg)
            </label>
            <select 
              className="bg-dark-bg border border-border rounded-xl px-4 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-gradient-start/50 transition-all cursor-pointer"
              value={formData.weekly_rate}
              onChange={(e) => { setFormData({...formData, weekly_rate: parseFloat(e.target.value)}); }}
            >
              <option value={0}>Manter Peso</option>
              <option value={0.25}>0.25 kg / semana</option>
              <option value={0.5}>0.50 kg / semana</option>
              <option value={0.75}>0.75 kg / semana</option>
              <option value={1}>1.00 kg / semana</option>
            </select>
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-bold text-text-secondary uppercase tracking-wider ml-1">
            Seu Objetivo
          </label>
          <textarea 
            className="bg-dark-bg border border-border rounded-xl p-4 text-sm text-text-primary min-h-[100px] focus:outline-none focus:ring-2 focus:ring-gradient-start/50 transition-all resize-none"
            placeholder="Ex: Quero perder 5kg de gordura focando em manter massa muscular."
            value={formData.goal}
            onChange={(e) => { setFormData({...formData, goal: e.target.value}); }}
          />
        </div>

        <div className="flex justify-end">
          <Button variant="primary" size="lg" type="submit" isLoading={isSaving} className="px-10 shadow-orange">
            Salvar Perfil
          </Button>
        </div>
      </form>
    </section>
  );
}
