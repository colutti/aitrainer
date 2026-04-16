import { Button } from '@shared/components/ui/Button';
import { usePublicConfig } from '@shared/hooks/usePublicConfig';
import { ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

export const Hero = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { enableNewUserSignups } = usePublicConfig();

  return (
    <section className="pt-32 pb-16 md:pt-48 md:pb-24 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-primary/10 border border-primary/20 mb-6">
            <span className="text-xs font-semibold text-primary uppercase tracking-wider">
              {t('landing.hero.eyebrow')}
            </span>
          </div>

          <h1 className="font-display text-4xl sm:text-6xl font-bold text-text-primary mb-6 leading-tight tracking-tight">
            {t('landing.hero.title')}
          </h1>

          <p className="text-lg md:text-xl text-text-secondary mb-10 leading-relaxed max-w-2xl">
            {t('landing.hero.description')}
          </p>

          <div className="flex flex-col sm:flex-row gap-4">
            <Button
              onClick={() => { void navigate(enableNewUserSignups ? '/login?mode=register' : '/login'); }}
              variant="primary"
              size="lg"
              disabled={!enableNewUserSignups}
              className="bg-primary bg-none hover:bg-primary-hover shadow-none rounded-lg h-14 px-8 text-lg"
            >
              {t('landing.hero.cta')}
              <ChevronRight className="ml-2 w-5 h-5" />
            </Button>
            
            <Button
              onClick={() => {
                document.querySelector('#demo')?.scrollIntoView({ behavior: 'smooth' });
              }}
              variant="secondary"
              size="lg"
              className="rounded-lg border-border bg-dark-card h-14 px-8 text-lg"
            >
              {t('landing.hero.demo_cta')}
            </Button>
          </div>

          <div className="mt-8 flex flex-wrap gap-6 text-sm text-text-muted">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-primary" />
              {t('landing.hero.proof_1')}
            </div>
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-primary" />
              {t('landing.hero.proof_2')}
            </div>
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-primary" />
              {t('landing.hero.proof_3')}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
