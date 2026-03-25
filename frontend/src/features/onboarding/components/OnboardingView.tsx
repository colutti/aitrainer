import { motion, AnimatePresence } from 'framer-motion';
import { 
  Check, 
  ArrowRight, 
  Dumbbell, 
  Database, 
  RefreshCw, 
  Lock,
  Zap,
  ChevronRight,
  ChevronLeft,
  Scale
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { Input } from '../../../shared/components/ui/Input';
import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { cn } from '../../../shared/utils/cn';
import { type OnboardingPayload } from '../api/onboarding-api';

interface OnboardingViewProps {
  step: number;
  onNext: () => void;
  onBack: () => void;
  onSubmit: () => Promise<void>;
  onFinish: () => void;
  formData: Partial<OnboardingPayload>;
  setFormData: (data: Partial<OnboardingPayload>) => void;
  loading: boolean;
  email: string;
  hevyApiKey: string;
  setHevyApiKey: (val: string) => void;
  onHevyConnect: () => Promise<void>;
  connectingHevy: boolean;
  onUpload: (file: File, type: 'mfp' | 'zepp') => Promise<void>;
  importing: string | null;
}

export function OnboardingView({
  step,
  onNext,
  onBack,
  onSubmit,
  onFinish,
  formData,
  setFormData,
  loading,
  hevyApiKey,
  setHevyApiKey,
  onHevyConnect,
  connectingHevy,
  onUpload,
  importing
}: OnboardingViewProps) {
  const { t } = useTranslation();

  const TRAINERS = [
    { id: 'atlas', name: 'Atlas', description: t('onboarding.trainers.atlas'), color: 'from-orange-500 to-red-600' },
    { id: 'luna', name: 'Luna', description: t('onboarding.trainers.luna'), color: 'from-indigo-400 to-purple-600' },
    { id: 'sargento', name: 'Sargento', description: t('onboarding.trainers.sargento'), color: 'from-slate-600 to-slate-800' },
    { id: 'sofia', name: 'Sofia', description: t('onboarding.trainers.sofia'), color: 'from-rose-400 to-pink-600' },
    { id: 'gymbro', name: 'GymBro', description: t('onboarding.trainers.gymbro'), color: 'from-yellow-400 to-orange-500' },
  ];

  const PLANS = [
    { id: 'Free', name: 'Free', icon: <Zap size={20} className="text-emerald-400" /> },
    { id: 'Basic', name: 'Basic', icon: <Zap size={20} className="text-blue-400" /> },
    { id: 'Pro', name: 'Pro', icon: <Zap size={20} className="text-orange-400" /> },
    { id: 'Premium', name: 'Premium', icon: <Zap size={20} className="text-purple-400" /> }
  ];

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
    exit: { opacity: 0, y: -20, transition: { duration: 0.3 } }
  };

  const renderStep = () => {
    switch(step) {
      case 2: // Profile
        return (
          <motion.div key="step2" variants={containerVariants} initial="hidden" animate="visible" exit="exit" className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-black text-white tracking-tight uppercase mb-2">{t('onboarding.step_2_title')}</h2>
              <p className="text-zinc-500 text-sm font-medium">{t('onboarding.step_2_subtitle')}</p>
            </div>

            <div className="space-y-6">
              <div className="space-y-3">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 ml-1">{t('settings.gender')}</label>
                <div className="grid grid-cols-2 gap-3">
                  {['male', 'female'].map((g) => (
                    <button
                      key={g}
                      type="button"
                      onClick={() => { setFormData({...formData, gender: t(`onboarding.genders.${g}`)}); }}
                      className={cn(
                        "py-4 rounded-2xl border font-bold transition-all text-sm",
                        formData.gender === t(`onboarding.genders.${g}`)
                          ? "bg-white/10 border-white/20 text-white shadow-xl shadow-white/5"
                          : "bg-white/[0.02] border-white/5 text-zinc-500 hover:border-white/10"
                      )}
                    >
                      {t(`onboarding.genders.${g}`)}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <Input 
                    id="onboarding-name"
                    data-testid="onboarding-name"
                    label={t('settings.name')} 
                    placeholder={t('onboarding.name_placeholder')} 
                    value={formData.name ?? ''}
                    onChange={e => { setFormData({...formData, name: e.target.value}); }}
                    className="h-14 bg-white/5 border-white/5 rounded-2xl focus:border-white/20"
                  />
                </div>
                <Input 
                  id="onboarding-age"
                  data-testid="onboarding-age"
                  label={t('onboarding.age')} 
                  type="number" 
                  value={formData.age ?? ''}
                  onChange={e => { setFormData({...formData, age: Number(e.target.value)}); }}
                  className="h-14 bg-white/5 border-white/5 rounded-2xl"
                />
                <Input 
                  id="onboarding-height"
                  data-testid="onboarding-height"
                  label={t('settings.height')} 
                  type="number" 
                  value={formData.height ?? ''}
                  onChange={e => { setFormData({...formData, height: Number(e.target.value)}); }}
                  className="h-14 bg-white/5 border-white/5 rounded-2xl"
                />
                <Input 
                  id="onboarding-weight"
                  data-testid="onboarding-weight"
                  label={t('body.weight.weight')} 
                  type="number" 
                  value={formData.weight ?? ''}
                  onChange={e => { setFormData({...formData, weight: Number(e.target.value)}); }}
                  className="h-14 bg-white/5 border-white/5 rounded-2xl md:col-span-2"
                />
              </div>
            </div>

            <Button 
              fullWidth 
              size="lg" 
              onClick={() => { onNext(); }} 
              disabled={!formData.gender || !formData.name || !formData.age || !formData.height || !formData.weight}
              className="h-14 rounded-2xl bg-white text-black font-black shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all"
            >
              {t('onboarding.next')}
              <ChevronRight className="ml-2 w-5 h-5" />
            </Button>
          </motion.div>
        );

      case 3: // Plan
        return (
          <motion.div key="step3" variants={containerVariants} initial="hidden" animate="visible" exit="exit" className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-black text-white tracking-tight uppercase mb-2">{t('onboarding.step_plan_title')}</h2>
              <p className="text-zinc-500 text-sm font-medium">{t('onboarding.step_plan_subtitle')}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {PLANS.map((plan) => (
                <PremiumCard
                  key={plan.id}
                  onClick={() => { setFormData({ ...formData, subscription_plan: plan.id }); }}
                  className={cn(
                    "p-6 cursor-pointer border transition-all relative overflow-hidden group",
                    formData.subscription_plan === plan.id
                      ? "bg-white/10 border-white/20 ring-1 ring-white/20"
                      : "bg-white/[0.02] border-white/5 hover:border-white/10"
                  )}
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-3 rounded-xl bg-black/20 border border-white/5">
                      {plan.icon}
                    </div>
                    {formData.subscription_plan === plan.id && (
                      <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center text-white">
                        <Check size={14} strokeWidth={4} />
                      </div>
                    )}
                  </div>
                  <h3 className="text-xl font-black text-white mb-1 uppercase tracking-tight">{plan.name}</h3>
                  <p className="text-[10px] text-zinc-500 font-bold leading-tight uppercase tracking-wider">
                    {t(`landing.plans.items.${plan.id.toLowerCase()}.description`)}
                  </p>
                </PremiumCard>
              ))}
            </div>

            <div className="flex gap-4">
              <button onClick={() => { onBack(); }} className="p-4 rounded-2xl bg-white/5 border border-white/5 text-zinc-400 hover:text-white transition-all">
                <ChevronLeft size={24} />
              </button>
              <Button 
                fullWidth 
                size="lg" 
                onClick={() => { onNext(); }}
                className="h-14 rounded-2xl bg-white text-black font-black shadow-2xl"
              >
                {t('onboarding.next')}
                <ChevronRight className="ml-2 w-5 h-5" />
              </Button>
            </div>
          </motion.div>
        );

      case 4: // Trainer
        return (
          <motion.div key="step4" variants={containerVariants} initial="hidden" animate="visible" exit="exit" className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-black text-white tracking-tight uppercase mb-2">{t('onboarding.step_3_title')}</h2>
              <p className="text-zinc-500 text-sm font-medium">{t('onboarding.step_3_subtitle')}</p>
            </div>

            <div className="space-y-3">
              {TRAINERS.map(trainer => {
                const isLocked = formData.subscription_plan === "Free" && trainer.id !== "gymbro";
                const isSelected = formData.trainer_type === trainer.id;
                
                return (
                  <PremiumCard
                    key={trainer.id}
                    onClick={() => { if (!isLocked) setFormData({...formData, trainer_type: trainer.id}); }}
                    className={cn(
                      "p-4 cursor-pointer transition-all flex items-center gap-4 relative overflow-hidden group",
                      isSelected ? "bg-white/10 border-white/20 shadow-xl" : "bg-white/[0.02] border-white/5",
                      isLocked && "opacity-40 grayscale cursor-not-allowed"
                    )}
                  >
                    <div className="relative">
                      <div className="w-16 h-16 rounded-full overflow-hidden border-2 border-white/10 bg-zinc-900">
                        <img src={`/assets/avatars/${trainer.id}.png`} alt={trainer.name} className="w-full h-full object-cover" />
                      </div>
                      {isSelected && (
                        <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-indigo-500 border-2 border-zinc-900 flex items-center justify-center text-white">
                          <Check size={12} strokeWidth={4} />
                        </div>
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-0.5">
                        <h4 className="font-black text-white uppercase tracking-tight">{trainer.name}</h4>
                        {isLocked && <Lock size={12} className="text-zinc-600" />}
                      </div>
                      <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider leading-relaxed line-clamp-2">
                        {trainer.description}
                      </p>
                    </div>
                    {isLocked && (
                      <span className="text-[9px] font-black uppercase bg-white/5 border border-white/10 px-2 py-1 rounded-full text-zinc-500">PRO</span>
                    )}
                  </PremiumCard>
                );
              })}
            </div>

            <div className="flex gap-4">
              <button onClick={() => { onBack(); }} className="p-4 rounded-2xl bg-white/5 border border-white/5 text-zinc-400 hover:text-white transition-all">
                <ChevronLeft size={24} />
              </button>
              <Button 
                fullWidth 
                size="lg" 
                onClick={() => { void onSubmit(); }} 
                isLoading={loading}
                className="h-14 rounded-2xl bg-white text-black font-black shadow-2xl"
              >
                {t('onboarding.next')}
                <ChevronRight className="ml-2 w-5 h-5" />
              </Button>
            </div>
          </motion.div>
        );

      case 5: // Integrations
        return (
          <motion.div key="step5" variants={containerVariants} initial="hidden" animate="visible" exit="exit" className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-black text-white tracking-tight uppercase mb-2">{t('onboarding.integrations_title')}</h2>
              <p className="text-zinc-500 text-sm font-medium">{t('onboarding.integrations_desc')}</p>
            </div>

            <div className="space-y-4">
              {/* Hevy Bento Card */}
              <PremiumCard className="p-6 bg-gradient-to-br from-indigo-500/10 to-transparent border-white/10">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2.5 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/20 shadow-inner">
                    <Dumbbell size={20} />
                  </div>
                  <div>
                    <h3 className="font-black text-white uppercase tracking-tight">Hevy Workouts</h3>
                    <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">{t('onboarding.integrations_hevy_desc')}</p>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <Input 
                    value={hevyApiKey}
                    onChange={e => { setHevyApiKey(e.target.value); }}
                    placeholder="Hevy API Key"
                    className="flex-1 h-12 bg-black/20 border-white/5 focus:border-white/20 rounded-xl text-sm font-bold"
                  />
                  <button 
                    onClick={() => { void onHevyConnect(); }} 
                    disabled={!hevyApiKey || connectingHevy}
                    className="px-6 rounded-xl bg-indigo-500 text-white font-black hover:bg-indigo-600 active:scale-95 transition-all shadow-lg shadow-indigo-500/20"
                  >
                    {connectingHevy ? <RefreshCw className="animate-spin" size={18} /> : t('common.connect')}
                  </button>
                </div>
              </PremiumCard>

              {/* CSV Import Bento Cards */}
              <div className="grid grid-cols-2 gap-4">
                <PremiumCard className="p-5 flex flex-col items-center text-center group cursor-pointer hover:bg-white/[0.04] transition-all">
                  <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500 mb-3 shadow-inner group-hover:scale-110 transition-transform">
                    <Database size={24} />
                  </div>
                  <h4 className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em] mb-3">MyFitnessPal</h4>
                  <label className="w-full">
                    <div className="py-2.5 rounded-xl bg-white/5 border border-white/5 text-[10px] font-black uppercase text-zinc-500 group-hover:text-white group-hover:bg-white/10 transition-all">
                      {importing === 'mfp' ? <RefreshCw size={14} className="animate-spin mx-auto" /> : 'Upload CSV'}
                    </div>
                    <input type="file" accept=".csv" className="hidden" onChange={e => {
                      const file = e.target.files?.[0];
                      if (file) void onUpload(file, 'mfp');
                    }} disabled={importing !== null} />
                  </label>
                </PremiumCard>

                <PremiumCard className="p-5 flex flex-col items-center text-center group cursor-pointer hover:bg-white/[0.04] transition-all">
                  <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-500 mb-3 shadow-inner group-hover:scale-110 transition-transform">
                    <Scale size={24} />
                  </div>
                  <h4 className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em] mb-3">Zepp Life</h4>
                  <label className="w-full">
                    <div className="py-2.5 rounded-xl bg-white/5 border border-white/5 text-[10px] font-black uppercase text-zinc-500 group-hover:text-white group-hover:bg-white/10 transition-all">
                      {importing === 'zepp' ? <RefreshCw size={14} className="animate-spin mx-auto" /> : 'Upload CSV'}
                    </div>
                    <input type="file" accept=".csv" className="hidden" onChange={e => {
                      const file = e.target.files?.[0];
                      if (file) void onUpload(file, 'zepp');
                    }} disabled={importing !== null} />
                  </label>
                </PremiumCard>
              </div>
            </div>

            <div className="flex flex-col gap-3 pt-2">
              <Button 
                fullWidth 
                size="lg" 
                onClick={() => { onNext(); }}
                className="h-14 rounded-2xl bg-white text-black font-black shadow-2xl hover:scale-[1.02] transition-all"
              >
                {t('onboarding.finish')}
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </div>
          </motion.div>
        );

      case 6: // Success
        return (
          <motion.div key="step6" variants={containerVariants} initial="hidden" animate="visible" exit="exit" className="space-y-8 text-center">
            <div className="relative mx-auto w-32 h-32 mb-8">
              <motion.div 
                initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', damping: 12, stiffness: 200 }}
                className="w-full h-full rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-500 shadow-[0_0_50px_rgba(16,185,129,0.2)]"
              >
                <Check size={64} strokeWidth={4} />
              </motion.div>
              <motion.div 
                animate={{ rotate: 360 }} transition={{ duration: 10, repeat: Infinity, ease: 'linear' }}
                className="absolute inset-0 border-2 border-dashed border-emerald-500/30 rounded-full"
              />
            </div>
            
            <div className="space-y-3">
              <h1 className="text-4xl font-black text-white tracking-tighter uppercase">{t('onboarding.success_title')}</h1>
              <p className="text-zinc-500 font-bold uppercase tracking-widest text-xs leading-relaxed max-w-sm mx-auto">
                {t('onboarding.success_desc', { name: formData.name ?? '' })}
              </p>
            </div>

            <Button 
              fullWidth 
              size="lg" 
              onClick={onFinish}
              className="mt-8 h-16 rounded-[2rem] bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-black text-lg shadow-2xl shadow-emerald-500/20 hover:scale-[1.02] active:scale-[0.98] transition-all uppercase tracking-widest"
            >
              {t('onboarding.go_to_dashboard')}
            </Button>
          </motion.div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] flex items-center justify-center p-6 relative overflow-hidden selection:bg-white/20">
      {/* Background Ambient Light */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-indigo-500/10 blur-[150px] pointer-events-none rounded-full" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-emerald-500/5 blur-[120px] pointer-events-none rounded-full" />

      <div className="w-full max-w-2xl relative z-10">
        {/* Progress Dots */}
        {step >= 2 && step < 6 && (
          <div className="flex justify-center gap-3 mb-12">
            {[2, 3, 4, 5].map((s) => (
              <div 
                key={s} 
                className={cn(
                  "h-1.5 rounded-full transition-all duration-500",
                  step === s ? "w-12 bg-white shadow-[0_0_10px_rgba(255,255,255,0.5)]" : 
                  step > s ? "w-4 bg-zinc-700" : "w-4 bg-zinc-800"
                )}
              />
            ))}
          </div>
        )}

        <AnimatePresence mode="wait">
          {renderStep()}
        </AnimatePresence>
      </div>
    </div>
  );
}
