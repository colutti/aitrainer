import { ChevronDown } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';

export const FAQ = () => {
  const { t } = useTranslation();
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const faqItems = t('landing.faq.items', { returnObjects: true }) as { q: string; a: string }[];

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 border-t border-border">
      <div className="max-w-2xl mx-auto">
        <h2 className="font-display text-3xl font-bold text-text-primary text-center mb-12">
          {t('landing.faq.title')}
        </h2>

        <div className="space-y-2">
          {faqItems.map((item, idx) => {
            const isOpen = openIndex === idx;
            return (
              <div 
                key={idx}
                className="border-b border-border last:border-0"
              >
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => { setOpenIndex(isOpen ? null : idx); }}
                  className="w-full h-auto flex items-center justify-between py-6 px-0 text-left group hover:bg-transparent"
                >
                  <span className={`text-base font-bold transition-colors ${isOpen ? 'text-primary' : 'text-text-primary group-hover:text-text-secondary'}`}>
                    {item.q}
                  </span>
                  <ChevronDown 
                    className={`w-4 h-4 text-text-muted transition-transform duration-200 ${
                      isOpen ? 'rotate-180 text-primary' : ''
                    }`} 
                  />
                </Button>
                <div 
                  className={`overflow-hidden transition-all duration-300 ${
                    isOpen ? 'max-h-96 opacity-100 mb-6' : 'max-h-0 opacity-0'
                  }`}
                >
                  <div className="text-text-secondary leading-relaxed text-sm">
                    {item.a}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
