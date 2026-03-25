import { Crown, ShieldCheck, Zap } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import { stripeApi } from '../../../shared/api/stripe-api';
import { STRIPE_PRICE_IDS } from '../../../shared/constants/stripe';
import { useAuthStore } from '../../../shared/hooks/useAuth';
import { useNotificationStore } from '../../../shared/hooks/useNotification';

import { SubscriptionView, type Plan } from './SubscriptionView';

/**
 * SubscriptionPage component (Container)
 * 
 * Manages plan selection and Stripe integration logic.
 * Delegates rendering to SubscriptionView.
 */
export default function SubscriptionPage() {
  const { t, i18n } = useTranslation();
  const { userInfo, loadUserInfo } = useAuthStore();
  const notify = useNotificationStore();
  const [loading, setLoading] = useState<string | null>(null);
  const [isInitialLoading, setIsInitialLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const refresh = async () => {
      try {
        await loadUserInfo();
      } finally {
        if (mounted) setIsInitialLoading(false);
      }
    };
    void refresh();
    return () => { mounted = false; };
  }, [loadUserInfo]);
  
  const isPt = i18n.language.startsWith('pt');
  const currentPlan = (userInfo?.subscription_plan ?? 'Free').toLowerCase().trim();

  const handleSubscribe = async (planId: string) => {
    const normalizedPlanId = planId.toLowerCase().trim();
    if (normalizedPlanId === 'free') return;
    
    setLoading(normalizedPlanId);
    try {
      const priceId = STRIPE_PRICE_IDS[normalizedPlanId as keyof typeof STRIPE_PRICE_IDS];
      if (!priceId) {
        throw new Error(`No price ID found for plan: ${normalizedPlanId}`);
      }

      const url = await stripeApi.createCheckoutSession(
        priceId,
        window.location.origin + '/dashboard?payment=success',
        window.location.origin + '/dashboard/settings/subscription?payment=cancel'
      );
      
      if (url) {
        window.location.assign(url);
      } else {
        throw new Error('No checkout URL returned from Stripe');
      }
    } catch (error) {
      console.error('Stripe error:', error);
      notify.error(t('settings.subscription.error', 'Erro ao iniciar pagamento'));
    } finally {
      setLoading(null);
    }
  };

  const handleManage = async (loadingKey = 'manage') => {
    setLoading(loadingKey);
    try {
      const url = await stripeApi.createPortalSession(window.location.origin + '/dashboard/settings/subscription');
      if (url) {
        window.location.assign(url);
      } else {
        throw new Error('No portal URL returned from Stripe');
      }
    } catch (error) {
      console.error('Portal error:', error);
      notify.error(t('settings.subscription.portal_error', 'Erro ao abrir portal de cobrança'));
    } finally {
      setLoading(null);
    }
  };

  const plans: Plan[] = [
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
      icon: Crown,
      features: t('landing.plans.items.premium.features', { returnObjects: true }) as string[],
    },
  ];

  return (
    <SubscriptionView 
      currentPlan={currentPlan}
      plans={plans}
      loading={loading}
      isInitialLoading={isInitialLoading}
      isPt={isPt}
      hasStripeCustomer={userInfo?.has_stripe_customer ?? false}
      onSubscribe={(id) => { void handleSubscribe(id); }}
      onManage={(key) => { void handleManage(key); }}
    />
  );
}
