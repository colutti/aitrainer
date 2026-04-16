import { stripeApi } from '@shared/api/stripe-api';
import { PlanCard } from '@shared/components/plans/PlanCard';
import { PLAN_CATALOG, buildPlanCardModel } from '@shared/constants/plan-catalog';
import { STRIPE_PRICE_IDS } from '@shared/constants/stripe';
import { useAuthStore } from '@shared/hooks/useAuth';
import { useNotificationStore } from '@shared/hooks/useNotification';
import { usePublicConfig } from '@shared/hooks/usePublicConfig';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

export const Pricing = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const { enableNewUserSignups } = usePublicConfig();
  const notify = useNotificationStore();
  const [loading, setLoading] = useState<string | null>(null);

  const isPt = i18n.language.startsWith('pt');
  const handleSubscribe = async (planId: string) => {
    if (!enableNewUserSignups) {
      notify.info(t('auth.new_signups_disabled'));
      return;
    }

    if (planId === 'free') {
      void navigate('/login?mode=register&plan=free');
      return;
    }

    if (!isAuthenticated) {
      void navigate(`/login?mode=register&plan=${planId}`);
      return;
    }

    setLoading(planId);
    try {
      const priceId = STRIPE_PRICE_IDS[planId as keyof typeof STRIPE_PRICE_IDS];
      const url = await stripeApi.createCheckoutSession(
        priceId,
        window.location.origin + '/dashboard?payment=success',
        window.location.origin + '/#planos'
      );
      window.location.assign(url);
    } catch (error) {
      console.error('Stripe error:', error);
      notify.error(t('settings.subscription.error', 'Erro ao iniciar pagamento'));
    } finally {
      setLoading(null);
    }
  };

  const plans = PLAN_CATALOG.map((entry) => buildPlanCardModel(entry, t, isPt));

  return (
    <section id="planos" className="py-20 px-4 sm:px-6 lg:px-8 border-t border-border">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="font-display text-3xl font-bold text-text-primary mb-4">
            {t('landing.plans.title')}
          </h2>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto">
            {t('landing.plans.subtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {plans.map((plan) => {
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
                  highlight: plan.highlight,
                }}
                context="marketing"
                actionLabel={plan.buttonLabel}
                onAction={() => {
                  void handleSubscribe(plan.id);
                }}
                disabled={loading !== null || !enableNewUserSignups}
                loading={loading === plan.id}
                actionTestId={`plan-button-${plan.id}`}
              />
            );
          })}
        </div>
      </div>
    </section>
  );
};
