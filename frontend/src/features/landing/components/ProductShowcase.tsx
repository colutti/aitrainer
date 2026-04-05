import { Button } from '@shared/components/ui/Button';
import { ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

export const ProductShowcase = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const dashboardHighlights = [
    t('landing.showcase.widgets.daily_target'),
    t('landing.showcase.widgets.metabolic_confidence'),
    t('landing.showcase.widgets.weight'),
    t('landing.showcase.widgets.fat'),
    t('landing.showcase.widgets.muscle'),
    t('landing.showcase.widgets.calories'),
    t('landing.showcase.widgets.recent_activity'),
    t('landing.showcase.widgets.weekly_frequency'),
    t('landing.showcase.widgets.prs'),
    t('landing.showcase.widgets.strength_radar'),
  ];

  const metabolismStats = [
    t('landing.showcase.metabolism_stats.target'),
    t('landing.showcase.metabolism_stats.confidence'),
    t('landing.showcase.metabolism_stats.balance'),
    t('landing.showcase.metabolism_stats.trend'),
    t('landing.showcase.metabolism_stats.consistency'),
    t('landing.showcase.metabolism_stats.stability'),
  ];

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 border-t border-border bg-dark-bg">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="font-display text-3xl font-bold text-text-primary mb-4">
            {t('landing.showcase.title')}
          </h2>
          <p className="text-lg text-text-secondary max-w-3xl mx-auto">
            {t('landing.showcase.description')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="rounded-2xl border border-border bg-light-bg p-6">
            <h3 className="text-lg font-bold text-text-primary mb-1">{t('landing.showcase.dashboard_title')}</h3>
            <p className="text-sm text-text-secondary mb-5">{t('landing.showcase.dashboard_subtitle')}</p>
            <div className="grid grid-cols-2 gap-2">
              {dashboardHighlights.map((item) => (
                <div key={item} className="rounded-md border border-border bg-dark-bg px-3 py-2 text-xs text-text-secondary">
                  {item}
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-light-bg p-6">
            <h3 className="text-lg font-bold text-text-primary mb-1">{t('landing.showcase.chat_title')}</h3>
            <p className="text-sm text-text-secondary mb-5">{t('landing.showcase.chat_subtitle')}</p>
            <div className="space-y-3">
              <div className="rounded-lg bg-primary text-white text-sm px-4 py-3">
                {t('landing.showcase.chat_example_user')}
              </div>
              <div className="rounded-lg border border-border bg-dark-bg text-sm text-text-secondary px-4 py-3">
                {t('landing.showcase.chat_example_trainer')}
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-light-bg p-6">
            <h3 className="text-lg font-bold text-text-primary mb-1">{t('landing.showcase.metabolism_title')}</h3>
            <p className="text-sm text-text-secondary mb-5">{t('landing.showcase.metabolism_subtitle')}</p>
            <div className="space-y-2">
              {metabolismStats.map((item) => (
                <div key={item} className="rounded-md border border-border bg-dark-bg px-3 py-2 text-xs text-text-secondary">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-16 text-center">
          <Button
            onClick={() => { void navigate('/login'); }}
            variant="secondary"
            className="border-border bg-dark-card rounded-md inline-flex items-center gap-2"
          >
            {t('landing.hero.demo_cta')}
            <ChevronRight size={16} />
          </Button>
        </div>
      </div>
    </section>
  );
};
