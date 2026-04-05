import { Button } from '@shared/components/ui/Button';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

export const StickyMobileCTA = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const scrollThreshold = 500;
      const isMobile = window.innerWidth < 768;
      setIsVisible(isMobile && window.scrollY > scrollThreshold);
    };

    window.addEventListener('scroll', handleScroll);
    return () => { window.removeEventListener('scroll', handleScroll); };
  }, []);

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-dark-bg border-t border-border flex md:hidden animate-fade-in">
      <Button
        onClick={() => { void navigate('/login?mode=register'); }}
        variant="primary"
        fullWidth
        className="h-12 bg-primary bg-none hover:bg-primary-hover shadow-none rounded-md"
      >
        {t('landing.hero.cta')}
      </Button>
    </div>
  );
};
