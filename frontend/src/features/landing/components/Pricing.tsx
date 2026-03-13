import { stripeApi } from '@shared/api/stripe-api';
import { Button } from '@shared/components/ui/Button';
import { STRIPE_PRICE_IDS } from '@shared/constants/stripe';
import { useAuthStore } from '@shared/hooks/useAuth';
import { useNotificationStore } from '@shared/hooks/useNotification';
import { Check } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

export const Pricing = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const notify = useNotificationStore();
  const [loading, setLoading] = useState<string | null>(null);

  const isPt = i18n.language.startsWith('pt');
  const currencySymbol = isPt ? 'R$ ' : '$';

  const handleSubscribe = async (planId: string) => {
    if (planId === 'free') {
      void navigate('/login?mode=register');
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
      window.location.href = url;
    } catch (error) {
      console.error('Stripe error:', error);
      notify.error(t('settings.subscription.error', 'Erro ao iniciar pagamento'));
    } finally {
      setLoading(null);
    }
  };

  const plans = [
    {
      id: 'free',
      price: 0,
      suffix: t('landing.plans.total', 'total'),
      isFree: true,
    },
    {
      id: 'basic',
      price: isPt ? 24.90 : 4.99,
      suffix: t('landing.plans.per_month', '/mês'),
      isFree: false,
    },
    {
      id: 'pro',
      price: isPt ? 49.90 : 9.99,
      suffix: t('landing.plans.per_month', '/mês'),
      isFree: false,
    },
    {
      id: 'premium',
      price: isPt ? 99.90 : 19.99,
      suffix: t('landing.plans.per_month', '/mês'),
      isFree: false,
    },
  ];

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

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map((plan) => {
            const planData = t(`landing.plans.items.${plan.id}`, { returnObjects: true }) as {
              name: string;
              description: string;
              features: string[];
              button: string;
            };

            return (
              <div key={plan.id} className="flex flex-col p-8 rounded-lg border border-border bg-dark-bg">
                <div className="mb-8">
                  <h3 className="text-xl font-bold text-text-primary mb-2">
                    {planData.name}
                  </h3>
                  <p className="text-sm text-text-secondary min-h-[40px]">
                    {planData.description}
                  </p>
                </div>

                <div className="mb-8">
                  <span className="text-3xl font-bold text-text-primary">
                    {plan.price === 0 
                      ? (isPt ? 'Grátis' : 'Free') 
                      : `${currencySymbol}${plan.price.toFixed(2).replace('.', isPt ? ',' : '.')}`}
                  </span>
                  {plan.price !== 0 && (
                    <span className="text-sm text-text-secondary ml-1">
                      {plan.suffix}
                    </span>
                  )}
                </div>

                <Button
                  onClick={() => { void handleSubscribe(plan.id); }}
                  variant={plan.id === 'pro' ? 'primary' : 'secondary'}
                  disabled={loading !== null}
                  isLoading={loading === plan.id}
                  fullWidth
                  className={`mb-8 rounded-md ${plan.id === 'pro' ? 'bg-primary bg-none hover:bg-primary-hover shadow-none' : 'border-border bg-dark-card'}`}
                  data-testid={`plan-button-${plan.id}`}
                >
                  {planData.button}
                </Button>

                <ul className="space-y-4">
                  {planData.features.slice(0, 6).map((feature, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-text-secondary">
                      <Check className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
