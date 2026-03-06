import { Activity, Utensils, Smartphone } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const IntegrationLogos = () => {
  const { t } = useTranslation();

  const integrations = [
    {
      name: 'Hevy',
      desc: t('landing.integrations_section.hevy_desc'),
      icon: Activity,
      color: 'text-orange-500',
      bgColor: 'bg-orange-500/10',
    },
    {
      name: 'MyFitnessPal',
      desc: t('landing.integrations_section.mfp_desc'),
      icon: Utensils,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
    },
    {
      name: 'Zepp Life',
      desc: t('landing.integrations_section.zepp_desc'),
      icon: Smartphone,
      color: 'text-pink-500',
      bgColor: 'bg-pink-500/10',
    },
  ];

  return (
    <section className="py-12 md:py-16 px-4 sm:px-6 lg:px-8 border-t border-white/5 bg-secondary/10">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="font-display text-3xl md:text-4xl font-bold text-white mb-4">
            {t('landing.integrations_section.title')}
          </h2>
          <p className="text-text-secondary max-w-2xl mx-auto">
            {t('landing.integrations_section.subtitle')}
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {integrations.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div 
                key={idx}
                className="group p-6 rounded-2xl border border-white/5 bg-secondary/40 hover:border-primary/30 transition-all duration-300"
              >
                <div className={`w-12 h-12 rounded-xl ${item.bgColor} ${item.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <Icon size={24} />
                </div>
                <h3 className="font-display font-bold text-white text-xl mb-2">{item.name}</h3>
                <p className="text-text-secondary text-sm leading-relaxed mb-4">
                  {item.desc}
                </p>
                <span className="text-[10px] font-bold uppercase tracking-widest text-primary/60">
                  {t('landing.integrations_section.coming_soon')}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
