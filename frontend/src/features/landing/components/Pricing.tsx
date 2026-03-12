import { Button } from '@shared/components/ui/Button';
import { Check } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

export const Pricing = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const isPt = i18n.language.startsWith('pt');
  const currencySymbol = isPt ? 'R$ ' : '$';

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
                  onClick={() => { void navigate('/login?mode=register'); }}
                  variant={plan.id === 'pro' ? 'primary' : 'secondary'}
                  disabled={!plan.isFree}
                  fullWidth
                  className={`mb-8 rounded-md ${plan.id === 'pro' ? 'bg-primary bg-none hover:bg-primary-hover shadow-none' : 'border-border bg-dark-card'}`}
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
