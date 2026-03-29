import { Check, CreditCard, Sparkles, AlertCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { Skeleton } from '../../../shared/components/ui/Skeleton';
import { PREMIUM_UI } from '../../../shared/styles/ui-variants';
import { cn } from '../../../shared/utils/cn';

export interface Plan {
  id: string;
  name: string;
  price: string;
  icon: React.ElementType;
  features: string[];
}

export interface SubscriptionViewProps {
  currentPlan: string;
  plans: Plan[];
  loading: string | null;
  isInitialLoading: boolean;
  isPt: boolean;
  hasStripeCustomer: boolean;
  isReadOnly?: boolean;
  onSubscribe: (planId: string) => void;
  onManage: (loadingKey?: string) => void;
}

export function SubscriptionView({
  currentPlan,
  plans,
  loading,
  isInitialLoading,
  isPt,
  hasStripeCustomer,
  isReadOnly = false,
  onSubscribe,
  onManage,
}: SubscriptionViewProps) {
  const { t } = useTranslation();

  if (isInitialLoading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="flex items-center gap-4">
           <Skeleton className="w-14 h-14 rounded-2xl bg-white/5" />
           <div className="space-y-2">
              <Skeleton className="h-4 w-32 bg-white/5" />
              <Skeleton className="h-8 w-64 bg-white/5" />
           </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
           {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-96 rounded-[32px] bg-white/5" />)}
        </div>
      </div>
    );
  }

  return (
    <div className={cn(PREMIUM_UI.animation.fadeIn, "space-y-10")}>
      {isReadOnly && (
        <PremiumCard className="p-4 border-amber-500/20 bg-amber-500/5 text-amber-200 text-[10px] font-black uppercase tracking-[0.2em]">
          Demo Read-Only
        </PremiumCard>
      )}
      
      {/* HEADER SECTION */}
      <div className="flex items-center gap-4">
        <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
          <CreditCard size={28} />
        </div>
        <div>
          <p className={PREMIUM_UI.text.label}>{t('settings.subscription.subtitle')}</p>
          <h1 className={PREMIUM_UI.text.heading}>{t('settings.subscription.title')}</h1>
        </div>
      </div>

      {/* PLANS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {plans.map((plan) => {
          const planIdLower = plan.id.toLowerCase().trim();
          const isCurrent = currentPlan === planIdLower;
          const Icon = plan.icon;
          
          return (
            <PremiumCard 
              key={plan.id} 
              className={cn(
                "p-8 flex flex-col h-full",
                isCurrent && "border-indigo-500/50 bg-indigo-500/[0.05] ring-1 ring-indigo-500/20"
              )}
            >
              <div className="mb-8">
                <div className={cn(
                  "w-12 h-12 rounded-2xl flex items-center justify-center mb-6 border transition-colors",
                  isCurrent 
                    ? "bg-indigo-500/20 text-indigo-400 border-indigo-500/30" 
                    : "bg-white/5 text-zinc-500 border-white/5"
                )}>
                  <Icon size={24} />
                </div>
                
                <h3 className="text-xl font-black text-white tracking-tight">{plan.name}</h3>
                
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="text-3xl font-black text-white tracking-tighter">
                    {isPt ? 'R$' : '$'}{plan.price}
                  </span>
                  <span className="text-[10px] text-zinc-500 font-black uppercase tracking-widest">
                    {t('common.per_month')}
                  </span>
                </div>
              </div>

              {isCurrent && (
                <div className="mb-6 px-3 py-1 bg-indigo-500 text-white text-[10px] font-black uppercase tracking-widest rounded-full self-start shadow-lg shadow-indigo-500/20 animate-in zoom-in-95">
                  {t('settings.subscription.active')}
                </div>
              )}

              <ul className="space-y-4 mb-10 flex-1">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex gap-3 text-xs font-medium text-zinc-400 leading-tight">
                    <div className="w-4 h-4 rounded-full bg-emerald-500/10 flex items-center justify-center shrink-0">
                       <Check size={10} className="text-emerald-400" strokeWidth={4} />
                    </div>
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                disabled={isReadOnly || isCurrent || planIdLower === 'free' || loading !== null}
                onClick={() => {
                  if (isReadOnly) return;
                  if (currentPlan !== 'free' && planIdLower !== 'free' && hasStripeCustomer) {
                    onManage(planIdLower);
                  } else {
                    onSubscribe(planIdLower);
                  }
                }}
                data-testid={`subscription-plan-btn-${planIdLower}`}
                className={cn(
                  "w-full py-4 rounded-full font-black text-sm transition-all flex items-center justify-center gap-2",
                  isCurrent 
                    ? "bg-white/5 text-zinc-500 border border-white/5 cursor-default" 
                    : planIdLower === 'free'
                      ? "bg-white/5 text-zinc-700 border border-white/5 cursor-not-allowed"
                      : "bg-white text-black hover:scale-105 active:scale-95 shadow-xl shadow-white/10"
                )}
              >
                {loading === planIdLower && <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />}
                <span>
                  {isCurrent 
                    ? t('settings.subscription.active') 
                    : planIdLower === 'free' 
                      ? t('settings.subscription.unavailable', 'Indisponível') 
                      : currentPlan !== 'free' && hasStripeCustomer
                        ? t('settings.subscription.change_plan')
                        : t('settings.subscription.upgrade')}
                </span>
              </button>
            </PremiumCard>
          );
        })}
      </div>

      {/* MANAGE SUBSCRIPTION CALLOUT */}
              {currentPlan !== 'free' && (
        <PremiumCard className="p-8 flex flex-col md:flex-row items-center justify-between gap-8 bg-gradient-to-r from-indigo-900/20 to-transparent border-indigo-500/20">
          <div className="flex items-center gap-5">
             <div className="w-14 h-14 bg-indigo-500/20 rounded-full flex items-center justify-center shrink-0 border border-indigo-500/30">
                <Sparkles size={28} className="text-indigo-400" />
             </div>
             <div>
                <h3 className="text-xl font-black text-white tracking-tight">{t('settings.subscription.manage_title')}</h3>
                <p className="text-sm text-zinc-500 font-medium leading-relaxed max-w-md">
                  {t('settings.subscription.manage_subtitle')}
                </p>
             </div>
          </div>
          
          <button 
            onClick={() => { if (!isReadOnly) onManage(); }} 
            disabled={isReadOnly || loading !== null}
            data-testid="btn-manage-subscription"
            className="w-full md:w-auto px-8 py-4 rounded-full bg-white/5 border border-white/10 text-white font-black hover:bg-white/10 transition-all flex items-center justify-center gap-2"
          >
            {loading === 'manage' && !isReadOnly && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />}
            {isReadOnly ? t('settings.subscription.read_only', 'Somente leitura') : t('settings.subscription.manage_button')}
          </button>
        </PremiumCard>
      )}

      {/* SECURITY BADGE */}
      <div className="flex items-center justify-center gap-2 text-zinc-600 opacity-50">
         <AlertCircle size={14} />
         <span className="text-[10px] font-bold uppercase tracking-[0.2em]">Pagamento Seguro via Stripe • Criptografia 256-bit</span>
      </div>
    </div>
  );
}
