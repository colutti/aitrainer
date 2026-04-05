import { Button } from '@shared/components/ui/Button';
import { LanguageSelector } from '@shared/components/ui/LanguageSelector';
import { Menu, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

export const Navbar = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => { window.removeEventListener('scroll', handleScroll); };
  }, []);

  const navLinks = [
    { name: t('landing.nav.demo'), href: '#demo' },
    { name: t('landing.nav.differentiators'), href: '#diferenciais' },
    { name: t('landing.nav.plans'), href: '#planos' },
  ];

  const handleNavClick = (href: string) => {
    setIsMenuOpen(false);
    const element = document.querySelector(href);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-colors duration-200 border-b ${
        scrolled
          ? 'bg-dark-bg border-border py-4'
          : 'bg-transparent border-transparent py-6'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        {/* Logo */}
        <div 
          className="flex items-center gap-2 cursor-pointer"
          onClick={() => { window.scrollTo({ top: 0, behavior: 'smooth' }); }}
        >
          <img src="/logo_icon.png" alt="FityQ" className="w-8 h-8" />
          <span className="font-display text-xl font-bold text-text-primary">
            FityQ
          </span>
        </div>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Button
              key={link.name}
              type="button"
              variant="ghost"
              onClick={() => { handleNavClick(link.href); }}
              className="h-auto p-0 text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-transparent transition-colors cursor-pointer"
            >
              {link.name}
            </Button>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-4">
          <LanguageSelector />
          <Button
            onClick={() => { void navigate('/login'); }}
            variant="secondary"
            size="sm"
            className="rounded-md border-border bg-dark-card"
          >
            {t('landing.nav.login')}
          </Button>
        </div>

        {/* Mobile menu toggle */}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="md:hidden text-text-primary p-2"
          onClick={() => { setIsMenuOpen(!isMenuOpen); }}
          aria-label="Toggle menu"
        >
          {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </Button>
      </div>

      {/* Mobile menu */}
      {isMenuOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 bg-dark-bg border-b border-border p-6 flex flex-col gap-6 animate-fade-in">
          {navLinks.map((link) => (
            <Button
              key={link.name}
              type="button"
              variant="ghost"
              onClick={() => { handleNavClick(link.href); }}
              className="h-auto justify-start p-0 text-lg font-medium text-text-primary hover:bg-transparent"
            >
              {link.name}
            </Button>
          ))}
          <div className="h-px bg-border" />
          <div className="flex items-center justify-between">
            <span className="text-sm text-text-secondary">{t('settings.language')}</span>
            <LanguageSelector />
          </div>
          <Button
            onClick={() => { void navigate('/login'); }}
            variant="secondary"
            fullWidth
            className="rounded-md border-border bg-dark-card"
          >
            {t('landing.nav.login')}
          </Button>
        </div>
      )}
    </nav>
  );
};
