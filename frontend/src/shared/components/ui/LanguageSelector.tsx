import { Globe, Check } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import { cn } from '../../utils/cn';

interface Language {
  code: string;
  label: string;
  flag: string;
  short: string;
}

const languages: Language[] = [
  { code: 'pt-BR', label: 'Português', flag: '🇧🇷', short: 'PT' },
  { code: 'es-ES', label: 'Español', flag: '🇪🇸', short: 'ES' },
  { code: 'en-US', label: 'English', flag: '🇺🇸', short: 'EN' },
];

/**
 * LanguageSelector component
 * 
 * A dropdown to switch application languages on the landing page.
 */
export function LanguageSelector() {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentLanguage = languages.find(lang => lang.code === i18n.language) ?? languages[0];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => { document.removeEventListener('mousedown', handleClickOutside); };
  }, []);

  const handleLanguageChange = (code: string) => {
    void i18n.changeLanguage(code);
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => { setIsOpen(!isOpen); }}
        className={cn(
          "flex items-center gap-2 px-3 py-2 rounded-xl transition-all duration-300",
          "hover:bg-white/10 text-text-secondary hover:text-white border border-transparent",
          isOpen && "bg-white/10 text-white border-white/10 shadow-lg"
        )}
        aria-haspopup="true"
        aria-expanded={isOpen}
      >
        <Globe size={18} className={cn("transition-transform duration-500", isOpen && "rotate-180")} />
        <span className="text-sm font-bold tracking-wider">{currentLanguage?.short}</span>
      </button>

      {isOpen && (
        <div 
          className="absolute right-0 mt-2 w-48 rounded-2xl bg-dark-card border border-white/10 shadow-2xl py-2 z-50 animate-in fade-in zoom-in-95 duration-200"
        >
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => { handleLanguageChange(lang.code); }}
              className={cn(
                "w-full flex items-center justify-between px-4 py-2.5 text-sm transition-colors",
                "hover:bg-white/5",
                i18n.language === lang.code ? "text-gradient-start font-bold" : "text-text-secondary"
              )}
            >
              <div className="flex items-center gap-3">
                <span className="text-lg leading-none">{lang.flag}</span>
                <span>{lang.label}</span>
              </div>
              {i18n.language === lang.code && <Check size={16} className="text-gradient-start" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
