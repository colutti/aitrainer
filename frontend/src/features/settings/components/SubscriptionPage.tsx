import { Check, CreditCard, Crown, ShieldCheck, Zap } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { stripeApi } from '../../../shared/api/stripe-api';
import { Button } from '../../../shared/components/ui/Button';
import { STRIPE_PRICE_IDS } from '../../../shared/constants/stripe';
import { useAuthStore } from '../../../shared/hooks/useAuth';
import { useNotificationStore } from '../../../shared/hooks/useNotification';

export function SubscriptionPage() {
  const { t, i18n } = useTranslation();
  const { userInfo } = useAuthStore();
  const notify = useNotificationStore();
  const [loading, setLoading] = useState<string | null>(null);
  
  const isPt = i18n.language.startsWith('pt');
  const currentPlan = userInfo?.subscription_plan ?? 'Free';

  const handleSubscribe = async (planId: string) => {
    if (planId === 'free') return;
    
    setLoading(planId);
    try {
      const priceId = STRIPE_PRICE_IDS[planId as keyof typeof STRIPE_PRICE_IDS];
      const url = await stripeApi.createCheckoutSession(
        priceId,
        window.location.origin + '/dashboard?payment=success',
        window.location.origin + '/settings/subscription?payment=cancel'
      );
      window.location.href = url;
    } catch (error) {
      console.error('Stripe error:', error);
      notify.error(t('settings.subscription.error'));
    } finally {
      setLoading(null);
    }
  };

  const handleManage = async () => {
    setLoading('manage');
    try {
      const url = await stripeApi.createPortalSession(window.location.origin + '/settings/subscription');
      window.location.href = url;
    } catch (error) {
      console.error('Portal error:', error);
      notify.error(t('settings.subscription.portal_error'));
    } finally {
      setLoading(null);
    }
  };

  const plans = [
    {
      id: 'free',
      name: t('landing.plans.items.free.name'),
      price: '0',
      icon: Zap,
      features: t('landing.plans.items.free.features', { returnObjects: true }) as string[],
    },
    {
      id: 'basic',
      name: t('landing.plans.items.basic.name'),
      price: isPt ? '24,90' : '4.99',
      icon: ShieldCheck,
      features: t('landing.plans.items.basic.features', { returnObjects: true }) as string[],
    },
    {
      id: 'pro',
      name: t('landing.plans.items.pro.name'),
      price: isPt ? '49,90' : '9.99',
      icon: Crown,
      features: t('landing.plans.items.pro.features', { returnObjects: true }) as string[],
    },
    {
      id: 'premium',
      name: t('landing.plans.items.premium.name'),
      price: isPt ? '99,90' : '19.99',
      icon: Crown, // Using Crown for premium for a more exclusive look
      features: t('landing.plans.items.premium.features', { returnObjects: true }) as string[],
    },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-primary/10 rounded-lg text-primary border border-primary/10">
          <CreditCard size={24} />
        </div>
        <div>
          <h1 className="text-2xl font-black text-text-primary tracking-tight">{t('settings.subscription.title', 'Assinatura')}</h1>
          <p className="text-text-secondary font-medium">{t('settings.subscription.subtitle', 'Gerencie seu plano e pagamentos')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {plans.map((plan) => {
          const isCurrent = currentPlan.toLowerCase() === plan.id.toLowerCase();
          
          return (
            <div 
              key={plan.id} 
              className={`p-6 rounded-xl border flex flex-col h-full bg-dark-card transition-colors duration-150 ${
                isCurrent ? 'border-primary' : 'border-border'
              }`}
            >
              <div className="mb-4">
                <div className={`w-10 h-10 rounded flex items-center justify-center mb-4 border ${
                  isCurrent ? 'bg-primary/20 text-primary border-primary/20' : 'bg-white/5 text-text-muted border-white/5'
                }`}>
                  <plan.icon size={20} />
                </div>
                <h3 className="text-lg font-black text-text-primary tracking-tight">{plan.name}</h3>
                <div className="mt-1">
                  <span className="text-2xl font-black text-text-primary tracking-tighter">{isPt ? 'R$' : '$'}{plan.price}</span>
                  <span className="text-[10px] text-text-muted ml-1 font-black uppercase">{t('common.per_month', '/mês')}</span>
                </div>
              </div>

              {isCurrent && (
                <div className="mb-4 px-3 py-1 bg-primary text-white text-[10px] font-black uppercase tracking-widest rounded self-start">
                  Plano Atual
                </div>
              )}

              <ul className="space-y-3 mb-8 flex-1">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex gap-2 text-xs text-text-secondary">
                    <Check size={14} className="text-primary shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <Button
                variant={isCurrent ? 'secondary' : plan.id === 'free' ? 'secondary' : 'primary'}
                disabled={isCurrent || plan.id === 'free' || loading !== null}
                isLoading={loading === plan.id}
                onClick={() => void handleSubscribe(plan.id)}
                className="w-full"
                data-testid={`subscription-plan-btn-${plan.id.toLowerCase()}`}
              >
                {isCurrent ? t('settings.subscription.active', 'Ativo') : plan.id === 'free' ? t('settings.subscription.unavailable', 'Indisponível') : t('settings.subscription.upgrade', 'Selecionar')}
              </Button>
            </div>
          );
        })}
      </div>

      {userInfo?.subscription_plan && userInfo.subscription_plan !== 'Free' && (
        <div className="bg-dark-card border border-border p-6 rounded-xl flex flex-col md:flex-row items-center justify-between gap-4 mt-8">
          <div>
            <h3 className="text-lg font-black text-text-primary tracking-tight">{t('settings.subscription.manage_title', 'Assinatura Ativa')}</h3>
            <p className="text-sm text-text-muted font-medium">{t('settings.subscription.manage_subtitle', 'Altere seu cartão ou cancele sua assinatura no portal do Stripe.')}</p>
          </div>
          <Button 
            variant="secondary" 
            onClick={() => void handleManage()} 
            isLoading={loading === 'manage'}
            className="w-full md:w-auto"
          >
            {t('settings.subscription.manage_button', 'Gerenciar Cobrança')}
          </Button>
        </div>
      )}
    </div>
  );
}
