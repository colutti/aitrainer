import { Dumbbell, User, Target, ChevronRight, Check, AlertTriangle, ArrowLeft } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { Button } from '../../../shared/components/ui/Button';
import { Input } from '../../../shared/components/ui/Input';
import { cn } from '../../../shared/utils/cn';
import { onboardingApi, OnboardingPayload } from '../api/onboarding-api';

const TRAINERS = [
  { id: 'atlas', name: 'Atlas', description: 'Treinador focado em força e intensidade brutal.', color: 'from-orange-500 to-red-600' },
  { id: 'luna', name: 'Luna', description: 'Foco em bem-estar, yoga e equilíbrio mental.', color: 'from-purple-500 to-pink-600' },
  { id: 'sargento', name: 'Sargento', description: 'Disciplina militar. Sem desculpas.', color: 'from-green-600 to-emerald-800' },
  { id: 'sofia', name: 'Sofia', description: 'Abordagem científica e baseada em dados.', color: 'from-blue-500 to-cyan-600' },
];

export function OnboardingPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const [step, setStep] = useState(0); // 0: Validating, 1: Password, 2: Profile, 3: Trainer
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState<Partial<OnboardingPayload>>({
    gender: 'Masculino',
    goal_type: 'maintain',
    weekly_rate: 0.5,
    trainer_type: 'atlas'
  });
  
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  useEffect(() => {
    if (!token) {
      setError('Token de convite não encontrado.');
      return;
    }
    
    async function validate() {
      if (!token) return;
      try {
        const res = await onboardingApi.validateToken(token);
        if (res.valid) {
          setStep(1);
        } else {
          setError(
            res.reason === 'expired' ? 'O convite expirou.' :
            res.reason === 'already_used' ? 'Convite já utilizado.' :
            'Convite inválido.'
          );
        }
      } catch {
        setError('Erro ao validar convite.');
      }
    }
    void validate();
  }, [token]);

  const handleNext = () => {
    setStep(s => s + 1);
  };

  const handleBack = () => {
    setStep(s => s - 1);
  };

  const handleSubmit = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const payload: OnboardingPayload = {
        token,
        password,
        gender: formData.gender ?? 'Masculino',
        age: Number(formData.age),
        weight: Number(formData.weight),
        height: Number(formData.height),
        goal_type: formData.goal_type ?? 'maintain',
        weekly_rate: Number(formData.weekly_rate),
        trainer_type: formData.trainer_type ?? 'atlas',
        name: formData.name
      };

      const res = await onboardingApi.completeOnboarding(payload);
      
      localStorage.setItem('jwt_token', res.token);
      window.location.href = '/'; // Hard redirect
    } catch {
      setError('Erro ao criar conta.');
      setLoading(false);
    }
  };

  const isPasswordValid = password.length >= 8 && /[0-9]/.test(password) && /[a-zA-Z]/.test(password);
  const passwordsMatch = password === confirmPassword;
  const canProceedStep1 = isPasswordValid && passwordsMatch;

  const canProceedStep2 = Number(formData.age) >= 18 && Number(formData.weight) > 0 && Number(formData.height) > 0;

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-dark-bg">
        <div className="bg-dark-card border border-red-500/20 p-8 rounded-2xl max-w-md w-full text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto text-red-500">
             <AlertTriangle size={32} />
          </div>
          <h1 className="text-xl font-bold text-text-primary">Erro no Cadastro</h1>
          <p className="text-text-secondary">{error}</p>
        </div>
      </div>
    );
  }

  if (step === 0) {
    return (
       <div className="min-h-screen flex items-center justify-center bg-dark-bg text-text-secondary">
          Validando convite...
       </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-dark-card border border-border rounded-3xl p-8 md:p-12 shadow-2xl animate-in fade-in zoom-in-95 duration-500">
        {/* Progress */}
        <div className="flex justify-between mb-8 relative">
           <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-zinc-800 -z-10" />
           {[1, 2, 3].map((s) => (
             <div 
               key={s} 
               className={cn(
                 "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors",
                 step >= s ? "bg-gradient-start text-white" : "bg-zinc-800 text-text-secondary"
               )}
             >
               {s}
             </div>
           ))}
        </div>

        {/* Step 1: Password */}
        {step === 1 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-text-primary text-center">Criar Senha</h2>
            <div className="space-y-4">
              <Input
                type="password"
                placeholder="Senha"
                value={password}
                onChange={e => { setPassword(e.target.value); }}
              />
              <Input
                type="password"
                placeholder="Confirmar Senha"
                value={confirmPassword}
                onChange={e => { setConfirmPassword(e.target.value); }}
              />
              <p className="text-xs text-text-muted">
                Min. 8 caracteres, números e letras.
              </p>
            </div>
            <Button fullWidth onClick={handleNext} disabled={!canProceedStep1}>
               Próximo
            </Button>
          </div>
        )}

        {/* Step 2: Profile */}
        {step === 2 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-text-primary text-center">Seu Perfil</h2>
            <div className="grid grid-cols-2 gap-4">
               <div className="col-span-2">
                 <label htmlFor="age" className="text-sm text-text-secondary">Idade</label>
                 <Input id="age" type="number" placeholder="Anos" 
                    value={formData.age || ''} 
                    onChange={e => { setFormData({...formData, age: Number(e.target.value)}); }} 
                 />
               </div>
               <div>
                 <label htmlFor="weight" className="text-sm text-text-secondary">Peso (kg)</label>
                 <Input id="weight" type="number" placeholder="kg"
                    value={formData.weight || ''}
                    onChange={e => { setFormData({...formData, weight: Number(e.target.value)}); }}
                 />
               </div>
               <div>
                  <label htmlFor="height" className="text-sm text-text-secondary">Altura (cm)</label>
                  <Input id="height" type="number" placeholder="cm"
                    value={formData.height || ''}
                    onChange={e => { setFormData({...formData, height: Number(e.target.value)}); }}
                  />
               </div>
            </div>
            <div className="flex gap-4">
               <Button variant="secondary" onClick={handleBack}>Voltar</Button>
               <Button className="flex-1" onClick={handleNext} disabled={!canProceedStep2}>Próximo</Button>
            </div>
          </div>
        )}

        {/* Step 3: Trainer */}
        {step === 3 && (
          <div className="space-y-6">
             <h2 className="text-2xl font-bold text-text-primary text-center">Escolha seu Treinador</h2>
             <div className="grid grid-cols-1 gap-3">
               {TRAINERS.map(t => (
                 <button
                   key={t.id}
                   onClick={() => { setFormData({...formData, trainer_type: t.id}); }}
                   className={cn(
                     "flex items-center gap-4 p-4 rounded-xl border text-left transition-all",
                     formData.trainer_type === t.id
                       ? "bg-gradient-start/10 border-gradient-start shadow-orange-sm"
                       : "bg-dark-bg border-border hover:border-zinc-600"
                   )}
                 >
                    <div className={cn("w-10 h-10 rounded-full bg-gradient-to-br", t.color)} />
                    <div>
                       <div className="font-bold text-text-primary">{t.name}</div>
                       <div className="text-xs text-text-secondary">{t.description}</div>
                    </div>
                    {formData.trainer_type === t.id && <Check className="ml-auto text-gradient-start" size={20} />}
                 </button>
               ))}
             </div>
             
             <div className="flex gap-4 mt-6">
                <Button variant="secondary" onClick={handleBack} disabled={loading}>Voltar</Button>
                <Button className="flex-1" onClick={() => void handleSubmit()} isLoading={loading}>
                   Finalizar Cadastro
                </Button>
             </div>
          </div>
        )}
      </div>
    </div>
  );
}
