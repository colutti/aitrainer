import { Activity, Smartphone, Utensils } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const IntegrationLogos = () => {
  const { t } = useTranslation();

  const integrations = [
    {
      name: 'Hevy',
      desc: t('landing.integrations_section.hevy_desc'),
      icon: Activity,
    },
    {
      name: 'MyFitnessPal',
      desc: t('landing.integrations_section.mfp_desc'),
      icon: Utensils,
    },
    {
      name: 'Zepp Life',
      desc: t('landing.integrations_section.zepp_desc'),
      icon: Smartphone,
    },
  ];

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 bg-light-bg border-t border-border">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="font-display text-3xl font-bold text-text-primary mb-4">
            {t('landing.integrations_section.title')}
          </h2>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto">
            {t('landing.integrations_section.subtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {integrations.map((item, idx) => (
            <div 
              key={idx}
              className="p-8 rounded-lg border border-border bg-dark-bg hover:border-primary/50 transition-colors"
            >
              <div className="w-12 h-12 rounded bg-primary/10 text-primary flex items-center justify-center mb-6">
                <item.icon size={24} />
              </div>
              <h3 className="text-xl font-bold text-text-primary mb-3">{item.name}</h3>
              <p className="text-text-secondary text-sm leading-relaxed mb-6">
                {item.desc}
              </p>
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">
                  {t('landing.integrations_section.coming_soon')}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
