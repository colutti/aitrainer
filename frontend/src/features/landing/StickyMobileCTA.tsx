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
      // Show after scrolling 500px, but only on mobile
      const scrollThreshold = 500;
      const isMobile = window.innerWidth < 768;
      setIsVisible(isMobile && window.scrollY > scrollThreshold);
    };

    window.addEventListener('scroll', handleScroll);
    return () => { window.removeEventListener('scroll', handleScroll); };
  }, []);

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-60 p-4 bg-dark-bg/80 backdrop-blur-lg border-t border-white/10 flex animate-in slide-in-from-bottom duration-300">
      <Button
        onClick={() => { void navigate('/login'); }}
        variant="primary"
        fullWidth
        className="h-12 shadow-lg shadow-primary/20"
      >
        {t('landing.sticky_cta')}
      </Button>
    </div>
  );
};
