import { Brain, Clock, LayoutGrid, MessageSquare, Users, Zap } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const Features = () => {
  const { t } = useTranslation();

  const features = [
    {
      icon: Zap,
      title: t('landing.diff.features.meta.title'),
      description: t('landing.diff.features.meta.description'),
    },
    {
      icon: Brain,
      title: t('landing.diff.features.vision.title'),
      description: t('landing.diff.features.vision.description'),
    },
    {
      icon: Users,
      title: t('landing.diff.features.trainers.title'),
      description: t('landing.diff.features.trainers.description'),
    },
    {
      icon: LayoutGrid,
      title: t('landing.diff.features.integrations.title'),
      description: t('landing.diff.features.integrations.description'),
    },
    {
      icon: MessageSquare,
      title: t('landing.diff.features.journey.title'),
      description: t('landing.diff.features.journey.description'),
    },
    {
      icon: Clock,
      title: t('landing.diff.features.available.title'),
      description: t('landing.diff.features.available.description'),
    },
  ];

  return (
    <section id="diferenciais" className="py-20 px-4 sm:px-6 lg:px-8 border-t border-border bg-light-bg">
      <div className="max-w-7xl mx-auto">
        <div className="mb-16">
          <h2 className="font-display text-3xl font-bold text-text-primary mb-4">
            {t('landing.diff.title')}
          </h2>
          <p className="text-lg text-text-secondary max-w-2xl">
            {t('landing.diff.subtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, idx) => (
            <div key={idx} className="p-8 rounded-lg border border-border bg-dark-bg hover:border-primary/50 transition-colors">
              <div className="w-10 h-10 rounded bg-primary/10 flex items-center justify-center mb-6 text-primary">
                <feature.icon size={20} />
              </div>
              <h3 className="text-lg font-bold text-text-primary mb-3">
                {feature.title}
              </h3>
              <p className="text-text-secondary text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
