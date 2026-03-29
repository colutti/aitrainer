import { ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const HowItWorks = () => {
  const { t } = useTranslation();

  const steps = t('landing.how.steps', { returnObjects: true }) as { title: string; desc: string }[];

  return (
    <section id="como-funciona" className="py-20 px-4 sm:px-6 lg:px-8 border-t border-border">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="font-display text-3xl font-bold text-text-primary mb-4">
            {t('landing.how.title')}
          </h2>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto">
            {t('landing.how.subtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
          {steps.map((item, idx) => (
            <div key={idx} className="relative group">
              <div className="font-display text-6xl font-black text-primary/10 mb-6 group-hover:text-primary transition-colors">
                {`0${(idx + 1).toString()}`}
              </div>
              <h3 className="text-2xl font-bold text-text-primary mb-4">
                {item.title}
              </h3>
              <p className="text-text-secondary leading-relaxed">
                {item.desc}
              </p>
              {idx < 2 && (
                <div className="hidden md:block absolute top-12 -right-6 text-border">
                  <ChevronRight size={32} />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
