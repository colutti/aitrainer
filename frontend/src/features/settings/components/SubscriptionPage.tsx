import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import { stripeApi } from '../../../shared/api/stripe-api';
import { PLAN_CATALOG, buildPlanCardModel } from '../../../shared/constants/plan-catalog';
import { STRIPE_PRICE_IDS } from '../../../shared/constants/stripe';
import { useAuthStore } from '../../../shared/hooks/useAuth';
import { useDemoMode } from '../../../shared/hooks/useDemoMode';
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
  const { isReadOnly: isDemoUser } = useDemoMode();
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
    if (isDemoUser) return;
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
    if (isDemoUser) return;
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
    ...PLAN_CATALOG.map((entry) => buildPlanCardModel(entry, t, isPt)),
  ];

  return (
    <SubscriptionView 
      currentPlan={currentPlan}
      plans={plans}
      loading={loading}
      isInitialLoading={isInitialLoading}
      hasStripeCustomer={userInfo?.has_stripe_customer ?? false}
      isReadOnly={isDemoUser}
      onSubscribe={(id) => { void handleSubscribe(id); }}
      onManage={(key) => { void handleManage(key); }}
    />
  );
}
