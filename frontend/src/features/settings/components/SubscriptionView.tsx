import { CreditCard, Sparkles, AlertCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { PlanCard } from '../../../shared/components/plans/PlanCard';
import { Button } from '../../../shared/components/ui/Button';
import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { Skeleton } from '../../../shared/components/ui/Skeleton';
import type { PlanCardModel } from '../../../shared/constants/plan-catalog';
import { PREMIUM_UI } from '../../../shared/styles/ui-variants';
import { cn } from '../../../shared/utils/cn';

const PLAN_PRIORITY: Record<string, number> = {
  free: 0,
  basic: 1,
  pro: 2,
};
const DEFAULT_READ_ONLY_MESSAGE = 'Demo Read-Only';

export type Plan = PlanCardModel;

export interface SubscriptionViewProps {
  currentPlan: string;
  plans: Plan[];
  loading: string | null;
  isInitialLoading: boolean;
  hasStripeCustomer: boolean;
  isReadOnly?: boolean;
  readOnlyLabel?: string;
  onSubscribe: (planId: string) => void;
  onManage: (loadingKey?: string) => void;
}

export function SubscriptionView({
  currentPlan,
  plans,
  loading,
  isInitialLoading,
  hasStripeCustomer,
  isReadOnly = false,
  readOnlyLabel,
  onSubscribe,
  onManage,
}: SubscriptionViewProps) {
  const { t } = useTranslation();

  const getPlanActionLabel = (targetPlanId: string, isCurrent: boolean) => {
    if (isCurrent) return t('settings.subscription.active');
    if (targetPlanId === 'free') return t('settings.subscription.unavailable', 'Indisponível');

    const currentPriority = PLAN_PRIORITY[currentPlan];
    const targetPriority = PLAN_PRIORITY[targetPlanId];

    if (currentPriority !== undefined && targetPriority !== undefined) {
      if (targetPriority > currentPriority) return t('settings.subscription.upgrade');
      if (targetPriority < currentPriority) return t('settings.subscription.downgrade');
      return t('settings.subscription.change_plan');
    }

    return currentPlan !== 'free' && hasStripeCustomer
      ? t('settings.subscription.change_plan')
      : t('settings.subscription.upgrade');
  };

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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
           {[1, 2, 3].map(i => <Skeleton key={i} className="h-96 rounded-[32px] bg-white/5" />)}
        </div>
      </div>
    );
  }

  return (
    <div className={cn(PREMIUM_UI.animation.fadeIn, "space-y-10")}>
      {isReadOnly && (
        <PremiumCard className="p-4 border-amber-500/20 bg-amber-500/5 text-amber-200 text-[10px] font-black uppercase tracking-[0.2em]">
          {readOnlyLabel ?? DEFAULT_READ_ONLY_MESSAGE}
        </PremiumCard>
      )}
      
      {/* HEADER SECTION */}
      <div className="flex items-center gap-4">
        <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
          <CreditCard size={28} />
        </div>
        <div>
          <h1 className={PREMIUM_UI.text.heading}>{t('settings.subscription.title')}</h1>
          <p className={PREMIUM_UI.text.label}>{t('settings.subscription.subtitle')}</p>
        </div>
      </div>

      {/* PLANS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {plans.map((plan) => {
          const planIdLower = plan.id.toLowerCase().trim();
          const isCurrent = currentPlan === planIdLower;

          return (
            <PlanCard
              key={plan.id}
              plan={{
                id: plan.id,
                name: plan.name,
                subtitle: plan.subtitle,
                priceLabel: plan.priceLabel,
                features: plan.features,
                badge: plan.badge,
                highlight: isCurrent || plan.highlight,
              }}
              context="management"
              current={isCurrent}
              actionLabel={getPlanActionLabel(planIdLower, isCurrent)}
              disabled={isReadOnly || isCurrent || planIdLower === 'free' || loading !== null}
              loading={loading === planIdLower}
              actionTestId={`subscription-plan-btn-${planIdLower}`}
              onAction={() => {
                if (isReadOnly) return;
                if (currentPlan !== 'free' && planIdLower !== 'free' && hasStripeCustomer) {
                  onManage(planIdLower);
                } else {
                  onSubscribe(planIdLower);
                }
              }}
              className="bg-black/20"
            />
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
          
          <Button
            type="button"
            onClick={() => { if (!isReadOnly) onManage(); }} 
            disabled={isReadOnly || loading !== null}
            data-testid="btn-manage-subscription"
            className="w-full md:w-auto px-8 py-4 rounded-full bg-white/5 border border-white/10 text-white font-black hover:bg-white/10 transition-all flex items-center justify-center gap-2"
          >
            {loading === 'manage' && !isReadOnly && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />}
            {isReadOnly ? t('settings.subscription.read_only', 'Somente leitura') : t('settings.subscription.manage_button')}
          </Button>
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
