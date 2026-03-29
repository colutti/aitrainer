import { useTranslation } from 'react-i18next';

export const Footer = () => {
  const { t } = useTranslation();

  return (
    <footer className="py-12 px-4 sm:px-6 lg:px-8 border-t border-border bg-dark-bg">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-8">
        <div className="flex items-center gap-2">
          <img src="/logo_icon.png" alt="FityQ" className="w-6 h-6" />
          <span className="font-display font-bold text-text-primary text-lg">FityQ</span>
        </div>
        
        <div className="flex items-center gap-8">
          <a href="#" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
            {t('landing.footer.terms')}
          </a>
          <a href="#" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
            {t('landing.footer.privacy')}
          </a>
          <a href="#" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
            {t('landing.footer.contact')}
          </a>
        </div>
        
        <p className="text-sm text-text-muted">
          {t('landing.footer.rights', { year: new Date().getFullYear() })}
        </p>
      </div>
    </footer>
  );
};
