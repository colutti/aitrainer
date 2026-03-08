import { Check, AlertTriangle, Dumbbell, Database, ArrowRight, Upload, Info, RefreshCw as RefreshIcon, Lock } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';

import { Button } from '../../../shared/components/ui/Button';
import { Input } from '../../../shared/components/ui/Input';
import { useAuthStore } from '../../../shared/hooks/useAuth';
import { useNotificationStore } from '../../../shared/hooks/useNotification';
import { cn } from '../../../shared/utils/cn';
import { integrationsApi } from '../../settings/api/integrations-api';
import { onboardingApi, type OnboardingPayload } from '../api/onboarding-api';

export function OnboardingPage() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const { userInfo } = useAuthStore();
  const notify = useNotificationStore();
  
  const TRAINERS = [
    { id: 'atlas', name: 'Atlas', description: t('onboarding.trainers.atlas', 'Especialista em biomecânica e precisão baseada em dados.'), color: 'from-orange-500 to-red-600' },
    { id: 'luna', name: 'Luna', description: t('onboarding.trainers.luna', 'Foco em bem-estar holístico, flexibilidade e atenção plena.'), color: 'from-indigo-400 to-purple-600' },
    { id: 'sargento', name: 'Sargento', description: t('onboarding.trainers.sargento', 'Treinador estilo bootcamp militar. Sem desculpas.'), color: 'from-slate-600 to-slate-800' },
    { id: 'sofia', name: 'Sofia', description: t('onboarding.trainers.sofia', 'Inteligência metabólica e saúde feminina empática.'), color: 'from-rose-400 to-pink-600' },
    { id: 'gymbro', name: 'GymBro', description: t('onboarding.trainers.gymbro', 'Parceiro de academia empolgado e motivacional!'), color: 'from-yellow-400 to-orange-500' },
  ];
  const token = searchParams.get('token');

  const [step, setStep] = useState(0); // 0: Validating, 1: Password, 2: Profile, 3: Plan, 4: Trainer, 5: Integrations, 6: Success
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState<Partial<OnboardingPayload>>({
    goal_type: 'maintain',
    weekly_rate: 0.5,
    trainer_type: 'atlas'
  });
  
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [email, setEmail] = useState('');
  const [hevyApiKey, setHevyApiKey] = useState('');
  const [connectingHevy, setConnectingHevy] = useState(false);
  const [importing, setImporting] = useState<string | null>(null);
  
  useEffect(() => {
    async function validate() {
      // Se o usuário já está autenticado e precisa de onboarding, pula validação de token
      if (userInfo && !userInfo.onboarding_completed) {
        setStep(2);
        return;
      }

      if (!token) {
        setError(t('onboarding.tokens.not_found'));
        return;
      }
      
      try {
        const res = await onboardingApi.validateToken(token);
        if (res.valid && res.email) {
          setEmail(res.email);
          setStep(1);
        } else if (res.valid) {
          setError(t('onboarding.tokens.invalid_response'));
        } else {
          setError(
            res.reason === 'expired' ? t('onboarding.tokens.expired') :
            res.reason === 'already_used' ? t('onboarding.tokens.already_used') :
            t('onboarding.tokens.invalid')
          );
        }
      } catch {
        setError(t('onboarding.tokens.validation_error'));
      }
    }
    void validate();
  }, [token, t, userInfo]);

  const handleNext = () => {
    setStep(s => s + 1);
  };

  const handleBack = () => {
    setStep(s => s - 1);
  };

  const handleSubmitProfile = async () => {
    setLoading(true);
    try {
      const payload = {
        gender: formData.gender ?? t('onboarding.genders.male'),
        age: Number(formData.age),
        weight: Number(formData.weight),
        height: Number(formData.height),
        goal_type: formData.goal_type ?? 'maintain',
        weekly_rate: Number(formData.weekly_rate),
        trainer_type: formData.trainer_type ?? 'atlas',
        name: formData.name
      };

      if (userInfo && !userInfo.onboarding_completed) {
        // Fluxo Público (já logado)
        const res = await onboardingApi.completePublicOnboarding(payload);
        localStorage.setItem('auth_token', res.token);
        setStep(5); // Vai para Integrações
      } else {
        // Fluxo por Convite
        if (!token || !email) return;
        
        const { auth } = await import('../../../features/auth/firebase');
        const { createUserWithEmailAndPassword } = await import('firebase/auth');
        
        try {
          await createUserWithEmailAndPassword(auth, email, password);
        } catch (err: unknown) {
          const errorCode = err instanceof Error && 'code' in err ? (err as { code: string }).code : '';
          if (errorCode !== 'auth/email-already-in-use') throw err;
        }

        const fullPayload = { ...payload, token, password };
        const res = await onboardingApi.completeOnboarding(fullPayload);
        localStorage.setItem('auth_token', res.token);
        setStep(5); // Vai para Integrações
      }
    } catch (err: unknown) {
      console.error('Onboarding completion error:', err);
      const errorCode = err instanceof Error && 'code' in err ? (err as { code: string }).code : '';
      setError(
        errorCode === 'auth/weak-password' ? t('onboarding.errors.weak_password') :
        t('onboarding.tokens.creation_error')
      );
    } finally {
      setLoading(false);
    }
  };

  const handleHevyConnect = async () => {
    if (!hevyApiKey) return;
    setConnectingHevy(true);
    try {
      await integrationsApi.saveHevyKey(hevyApiKey);
      const msg = t('onboarding.hevy_connected_success', 'Hevy conectado com sucesso!');
      notify.success(msg);
    } catch (error) {
      console.error('Hevy connect error:', error);
      notify.error(t('onboarding.hevy_error_connect', 'Erro ao conectar Hevy. Verifique sua chave de API.'));
    } finally {
      setConnectingHevy(false);
    }
  };

  const handleUpload = async (file: File, type: 'mfp' | 'zepp') => {
    setImporting(type);
    try {
      const res = type === 'mfp' 
        ? await integrationsApi.uploadMfpCsv(file)
        : await integrationsApi.uploadZeppLifeCsv(file);
        
      notify.success(t('onboarding.import_success', 'Importação concluída com sucesso! {{created}} novos registros.', { 
        created: String(res.created) 
      }));
    } catch (err) {
      console.error(err);
      notify.error(t('onboarding.import_error', 'Erro ao importar arquivo.'));
    } finally {
      setImporting(null);
    }
  };

  const isPasswordValid = password.length >= 8 && /[0-9]/.test(password) && /[a-z]/.test(password) && /[A-Z]/.test(password);
  const passwordsMatch = password === confirmPassword;
  const canProceedStep1 = isPasswordValid && passwordsMatch;

  const canProceedStep2 = !!formData.gender && Number(formData.age) >= 18 && Number(formData.weight) > 0 && Number(formData.height) > 0;

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-dark-bg">
        <div className="bg-dark-card border border-red-500/20 p-8 rounded-2xl max-w-md w-full text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto text-red-500">
             <AlertTriangle size={32} />
          </div>
          <h1 className="text-xl font-bold text-text-primary">{t('onboarding.error_title')}</h1>
          <p className="text-text-secondary">{error}</p>
        </div>
      </div>
    );
  }

  if (step === 0) {
    return (
       <div className="min-h-screen flex items-center justify-center bg-dark-bg text-text-secondary">
          {t('onboarding.validating')}
       </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-dark-card border border-border rounded-3xl p-8 md:p-12 shadow-2xl animate-in fade-in zoom-in-95 duration-500">
        {/* Progress */}
        {step < 6 && step > 1 && (
          <div className="flex justify-between mb-8 relative">
            <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-zinc-800 -z-10" />
            {[2, 3, 4, 5].map((s) => (
              <div 
                key={s} 
                className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors",
                  step >= s ? "bg-gradient-start text-white" : "bg-zinc-800 text-text-secondary"
                )}
              >
                {s - 1}
              </div>
            ))}
          </div>
        )}

        {/* Step 1: Password */}
        {step === 1 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-text-primary text-center">{t('onboarding.step_1_title')}</h2>
            <div className="space-y-4">
              <Input
                id="password"
                label={t('onboarding.password_placeholder')}
                type="password"
                placeholder={t('onboarding.password_placeholder')}
                value={password}
                onChange={e => { setPassword(e.target.value); }}
              />
              <Input
                id="confirmPassword"
                label={t('onboarding.confirm_password_placeholder')}
                type="password"
                placeholder={t('onboarding.confirm_password_placeholder')}
                value={confirmPassword}
                onChange={e => { setConfirmPassword(e.target.value); }}
              />
              <p className="text-xs text-zinc-400">
                {t('onboarding.password_hint')}
              </p>
            </div>
            <Button fullWidth onClick={handleNext} disabled={!canProceedStep1}>
               {t('onboarding.next')}
            </Button>
          </div>
        )}

        {/* Step 2: Profile */}
        {step === 2 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-text-primary text-center">{t('onboarding.step_2_title')}</h2>
            
            <div className="space-y-4">
               {/* Gender Selection */}
               <div className="space-y-2">
                 <label className="text-sm text-text-secondary">{t('settings.gender')}</label>
                 <div className="grid grid-cols-2 gap-3">
                   {['male', 'female'].map((g) => (
                     <button
                       key={g}
                       type="button"
                       onClick={() => { setFormData({...formData, gender: t(`onboarding.genders.${g}`)}); }}
                       className={cn(
                         "py-3 px-4 rounded-xl border font-medium transition-all text-sm",
                         formData.gender === t(`onboarding.genders.${g}`)
                           ? "bg-gradient-start/10 border-gradient-start text-gradient-start"
                           : "bg-dark-bg border-border text-text-secondary hover:border-zinc-600"
                       )}
                     >
                       {t(`onboarding.genders.${g}`)}
                     </button>
                   ))}
                 </div>
               </div>

               <div className="grid grid-cols-2 gap-4">
                 <div className="col-span-2">
                   <label htmlFor="age" className="text-sm text-text-secondary">{t('onboarding.age')}</label>
                   <Input id="age" type="number" placeholder={t('onboarding.age_placeholder')} 
                      value={formData.age ?? ''} 
                      onChange={e => { setFormData({...formData, age: Number(e.target.value)}); }} 
                   />
                 </div>
                 <div>
                   <label htmlFor="weight" className="text-sm text-text-secondary">{t('body.weight.weight').split(' ')[0]}</label>
                   <Input id="weight" type="number" placeholder={t('onboarding.weight_placeholder')}
                       value={formData.weight ?? ''}
                      onChange={e => { setFormData({...formData, weight: Number(e.target.value)}); }}
                   />
                 </div>
                 <div>
                    <label htmlFor="height" className="text-sm text-text-secondary">{t('settings.height').split(' ')[0]}</label>
                    <Input id="height" type="number" placeholder={t('onboarding.height_placeholder')}
                       value={formData.height ?? ''}
                      onChange={e => { setFormData({...formData, height: Number(e.target.value)}); }}
                    />
                 </div>
               </div>
            </div>

            <div className="flex gap-4">
               <Button variant="secondary" onClick={handleBack}>{t('onboarding.back')}</Button>
               <Button className="flex-1" onClick={handleNext} disabled={!canProceedStep2}>{t('onboarding.next')}</Button>
            </div>
          </div>
        )}

        {/* Step 3: Plan */}
        {step === 3 && (
          <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
             <h2 className="text-2xl font-bold text-text-primary text-center">{t('onboarding.step_plan_title', 'Escolha seu Plano')}</h2>
             <div className="space-y-4">
                <button
                   onClick={() => { /* Already selected */ }}
                   className={cn(
                     "w-full flex flex-col p-6 rounded-2xl border transition-all text-left",
                     "bg-gradient-start/10 border-gradient-start shadow-orange-sm ring-1 ring-gradient-start"
                   )}
                >
                   <div className="flex justify-between items-center w-full mb-2">
                      <span className="font-bold text-xl text-text-primary">Free</span>
                      <span className="text-gradient-start font-bold uppercase text-xs tracking-wider">{t('onboarding.plan_free_badge', 'Gratuito')}</span>
                   </div>
                   <p className="text-sm text-text-secondary mb-4">{t('onboarding.plan_free_desc', 'Inicie com 20 mensagens por dia durante 7 dias para testar a plataforma.')}</p>
                   <div className="space-y-2 mt-auto">
                      <div className="flex items-center gap-2 text-sm text-text-secondary"><Check size={16} className="text-emerald-500" /> Acesso ao Gymbro AI</div>
                      <div className="flex items-center gap-2 text-sm text-text-secondary"><Check size={16} className="text-emerald-500" /> Dashboard & Análises Musculares</div>
                      <div className="flex items-center gap-2 text-sm text-text-secondary"><Check size={16} className="text-emerald-500" /> Integrações com Hevy / Outros</div>
                   </div>
                </button>
             </div>
             
             <div className="flex gap-4 mt-6">
                <Button variant="secondary" onClick={handleBack}>{t('onboarding.back')}</Button>
                <Button className="flex-1" onClick={() => {
                   if (formData.trainer_type !== 'gymbro') {
                       setFormData({ ...formData, trainer_type: 'gymbro' });
                   }
                   handleNext();
                }}>
                   {t('onboarding.next')}
                </Button>
             </div>
          </div>
        )}

        {/* Step 4: Trainer */}
        {step === 4 && (
          <div className="space-y-6">
             <h2 className="text-2xl font-bold text-text-primary text-center">{t('onboarding.step_3_title')}</h2>
             <div className="grid grid-cols-1 gap-3">
               {TRAINERS.map(trainer => {
                 const isLocked = trainer.id !== 'gymbro';
                 
                 return (
                 <button
                   key={trainer.id}
                   type="button"
                   disabled={isLocked}
                   onClick={() => { if (!isLocked) setFormData({...formData, trainer_type: trainer.id}); }}
                   className={cn(
                     "flex items-center gap-4 p-4 rounded-xl border text-left transition-all relative overflow-hidden",
                     formData.trainer_type === trainer.id
                       ? "bg-gradient-start/10 border-gradient-start shadow-orange-sm"
                       : "bg-dark-bg border-border hover:border-zinc-600",
                     trainer.id !== 'gymbro' && "opacity-60 grayscale hover:border-border cursor-not-allowed"
                   )}
                 >
                    <img src={`/assets/avatars/${trainer.id}.png`} alt={trainer.name} className="w-12 h-12 rounded-full border-2 border-dark-bg object-cover bg-white/10 relative z-10" />
                    <div className="relative z-10 flex-1">
                       <div className="font-bold text-text-primary flex items-center gap-2">
                           {trainer.name}
                           {isLocked && <Lock size={14} className="text-text-muted" />}
                       </div>
                       <div className="text-xs text-text-secondary pr-8">{trainer.description}</div>
                    </div>
                    {formData.trainer_type === trainer.id && <Check className="ml-auto text-gradient-start relative z-10" size={20} />}
                    {isLocked && (
                       <div className="absolute right-4 top-1/2 -translate-y-1/2">
                          <span className="text-[10px] font-bold uppercase tracking-wider bg-zinc-800 text-zinc-400 px-2 py-1 rounded-full">Pro</span>
                       </div>
                    )}
                 </button>
               );
               })}
             </div>
             <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl text-xs text-blue-200 text-center">
                 {t('onboarding.free_plan_trainer_hint', 'No plano gratuito o acesso é limitado ao treinador Gymbro. Mude seu plano para liberar outros treinadores após o Onboarding nas configurações.')}
             </div>
             
              <div className="flex gap-4 mt-6">
                <Button variant="secondary" onClick={handleBack} disabled={loading}>{t('onboarding.back')}</Button>
                <Button className="flex-1" onClick={() => void handleSubmitProfile()} isLoading={loading}>
                   {t('onboarding.next')}
                </Button>
              </div>
          </div>
        )}

        {/* Step 5: Integrations */}
        {step === 5 && (
          <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold text-text-primary">{t('onboarding.integrations_title')}</h2>
              <p className="text-sm text-text-secondary">{t('onboarding.integrations_desc')}</p>
            </div>

            <div className="space-y-4">
              {/* Hevy Sync */}
              <div className="bg-dark-bg/50 border border-border p-5 rounded-2xl space-y-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gradient-start/10 rounded-lg text-gradient-start">
                    <Dumbbell size={20} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-text-primary">Hevy API</h3>
                      <div className="group relative">
                        <Info size={14} className="text-text-muted cursor-help" />
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-zinc-800 text-[10px] text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl border border-white/5">
                          {t('onboarding.integrations_hevy_hint')}
                        </div>
                      </div>
                    </div>
                    <p className="text-xs text-text-secondary">{t('onboarding.integrations_hevy_desc')}</p>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <Input 
                    value={hevyApiKey}
                    onChange={e => { setHevyApiKey(e.target.value); }}
                    placeholder="Hevy API Key"
                    className="flex-1 h-10 text-sm"
                  />
                  <Button 
                    size="sm" 
                    onClick={() => void handleHevyConnect()} 
                    isLoading={connectingHevy}
                    disabled={!hevyApiKey}
                  >
                    {t('common.connect')}
                  </Button>
                </div>
              </div>

              {/* CSV Imports */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* MFP */}
                <div className="bg-dark-bg/30 border border-border/50 p-4 rounded-2xl space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Database size={16} className="text-emerald-500" />
                      <span className="text-xs font-bold text-text-primary uppercase">MyFitnessPal</span>
                    </div>
                    <div className="group relative">
                      <Info size={12} className="text-text-muted cursor-help" />
                      <div className="absolute bottom-full right-0 mb-2 w-48 p-2 bg-zinc-800 text-[10px] text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl border border-white/5">
                        {t('onboarding.integrations_mfp_hint', 'Exporte o CSV de Nutrição no site do MyFitnessPal e faça o upload aqui.')}
                      </div>
                    </div>
                  </div>
                  <label className="flex items-center justify-center w-full h-20 border border-dashed border-zinc-700 rounded-xl hover:bg-white/5 cursor-pointer transition-colors group">
                    {importing === 'mfp' ? (
                      <RefreshIcon size={16} className="animate-spin text-emerald-500" />
                    ) : (
                      <div className="flex flex-col items-center">
                        <Upload size={16} className="text-zinc-500 group-hover:text-emerald-500 transition-colors" />
                        <span className="text-[10px] text-text-secondary mt-1">Upload CSV</span>
                      </div>
                    )}
                    <input 
                      type="file" 
                      accept=".csv" 
                      className="hidden" 
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) void handleUpload(file, 'mfp');
                      }}
                      disabled={importing !== null}
                    />
                  </label>
                </div>

                {/* Zepp Life */}
                <div className="bg-dark-bg/30 border border-border/50 p-4 rounded-2xl space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Database size={16} className="text-indigo-500" />
                      <span className="text-xs font-bold text-text-primary uppercase">Zepp Life</span>
                    </div>
                    <div className="group relative">
                      <Info size={12} className="text-text-muted cursor-help" />
                      <div className="absolute bottom-full right-0 mb-2 w-48 p-2 bg-zinc-800 text-[10px] text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl border border-white/5">
                        {t('onboarding.integrations_zepp_hint', 'Exporte o CSV de Peso no app Zepp Life e faça o upload aqui.')}
                      </div>
                    </div>
                  </div>
                  <label className="flex items-center justify-center w-full h-20 border border-dashed border-zinc-700 rounded-xl hover:bg-white/5 cursor-pointer transition-colors group">
                    {importing === 'zepp' ? (
                      <RefreshIcon size={16} className="animate-spin text-indigo-500" />
                    ) : (
                      <div className="flex flex-col items-center">
                        <Upload size={16} className="text-zinc-500 group-hover:text-indigo-500 transition-colors" />
                        <span className="text-[10px] text-text-secondary mt-1">Upload CSV</span>
                      </div>
                    )}
                    <input 
                      type="file" 
                      accept=".csv" 
                      className="hidden" 
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) void handleUpload(file, 'zepp');
                      }}
                      disabled={importing !== null}
                    />
                  </label>
                </div>
              </div>

              {/* Settings Hint */}
              <div className="bg-orange-500/5 border border-orange-500/20 p-4 rounded-xl flex items-start gap-3">
                <AlertTriangle className="text-orange-500 shrink-0 mt-0.5" size={16} />
                <p className="text-[11px] text-orange-200/80 leading-snug">
                  {t('onboarding.integrations_settings_hint')}
                </p>
              </div>
            </div>

            <div className="flex flex-col gap-3 pt-2">
              <Button fullWidth onClick={handleNext} className="h-12">
                {t('onboarding.finish', 'Finalizar Onboarding')}
                <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
            </div>
          </div>
        )}

        {/* Step 6: Success */}
        {step === 6 && (
          <div className="space-y-8 text-center animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="w-20 h-20 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center mx-auto text-emerald-500 mb-2">
              <Check size={40} strokeWidth={3} />
            </div>
            
            <div className="space-y-3">
              <h1 className="text-3xl font-black text-white tracking-tight">
                {t('onboarding.success_title')}
              </h1>
              <p className="text-text-secondary leading-relaxed max-w-sm mx-auto">
                {t('onboarding.success_desc', { 
                  name: userInfo?.name ?? '', 
                  trainer: TRAINERS.find(t => t.id === formData.trainer_type)?.name ?? '' 
                })}
              </p>
            </div>

            <Button 
              fullWidth 
              size="lg" 
              onClick={() => { window.location.href = '/dashboard'; }}
              className="mt-4 shadow-[0_20px_50px_rgba(249,115,22,0.3)] h-14 text-lg"
            >
              {t('onboarding.go_to_dashboard')}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
