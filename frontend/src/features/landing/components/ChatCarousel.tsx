import { useTranslation } from 'react-i18next';

export const ChatCarousel = () => {
  const { t } = useTranslation();

  const steps = [
    {
      eyebrow: t('landing.demo.step_1_eyebrow'),
      title: t('landing.demo.step_1_title'),
      description: t('landing.demo.step_1_description'),
    },
    {
      eyebrow: t('landing.demo.step_2_eyebrow'),
      title: t('landing.demo.step_2_title'),
      description: t('landing.demo.step_2_description'),
    },
    {
      eyebrow: t('landing.demo.step_3_eyebrow'),
      title: t('landing.demo.step_3_title'),
      description: t('landing.demo.step_3_description'),
    },
  ];

  const contextPoints = t('landing.demo_case.context_points', { returnObjects: true }) as string[];

  return (
    <section id="demo" className="py-20 px-4 sm:px-6 lg:px-8 border-t border-border">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="font-display text-3xl font-bold text-text-primary mb-4">
            {t('landing.demo.title')}
          </h2>
          <p className="text-lg text-text-secondary max-w-3xl mx-auto">
            {t('landing.demo.subtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {steps.map((step) => (
            <div key={step.title} className="rounded-2xl border border-border bg-light-bg p-6">
              <p className="text-xs font-bold uppercase tracking-widest text-primary mb-3">{step.eyebrow}</p>
              <h3 className="text-xl font-bold text-text-primary mb-3">{step.title}</h3>
              <p className="text-sm text-text-secondary leading-relaxed">{step.description}</p>
            </div>
          ))}
        </div>

        <div className="rounded-2xl border border-border bg-dark-bg p-6 sm:p-8">
          <div className="text-xs font-bold uppercase tracking-widest text-primary mb-2">
            {t('landing.demo_case.label')}
          </div>
          <h3 className="text-2xl font-bold text-text-primary mb-6">{t('landing.demo_case.title')}</h3>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rounded-xl border border-border bg-light-bg p-5">
              <p className="text-xs font-bold uppercase tracking-widest text-text-muted mb-3">
                {t('landing.demo_case.context_title')}
              </p>
              <ul className="space-y-2">
                {contextPoints.map((point) => (
                  <li key={point} className="text-sm text-text-secondary leading-relaxed">
                    {point}
                  </li>
                ))}
              </ul>
            </div>

            <div className="rounded-xl border border-border bg-light-bg p-5">
              <p className="text-xs font-bold uppercase tracking-widest text-text-muted mb-2">
                {t('landing.demo_case.trainer_title')}
              </p>
              <p className="text-sm font-semibold text-primary mb-3">{t('landing.demo_case.trainer_name')}</p>
              <p className="text-sm text-text-secondary leading-relaxed">{t('landing.demo_case.trainer_reply')}</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
