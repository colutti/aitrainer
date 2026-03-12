import { Button } from '@shared/components/ui/Button';
import { ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

export const FinalCTA = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8 bg-primary/5 border-t border-border">
      <div className="max-w-3xl mx-auto text-center">
        <h2 className="font-display text-4xl font-bold text-text-primary mb-6">
          {t('landing.cta.title')}
        </h2>
        <p className="text-lg text-text-secondary mb-10">
          {t('landing.cta.subtitle')}
        </p>
        <Button
          onClick={() => { void navigate('/login?mode=register'); }}
          variant="primary"
          size="lg"
          className="bg-primary bg-none hover:bg-primary-hover shadow-none rounded-lg h-14 px-10 text-lg"
        >
          {t('landing.cta.button')}
          <ChevronRight size={20} className="ml-2" />
        </Button>
        <p className="text-xs text-text-muted mt-6 uppercase font-bold tracking-widest">
          {t('landing.cta.trial')}
        </p>
      </div>
    </section>
  );
};
