import { ChevronDown } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

export const FAQAccordion = () => {
  const { t } = useTranslation();
  const [openIndex, setOpenIndex] = useState<number | null>(null);

    const faqItems = t('landing.faq.items', { returnObjects: true }) as { q: string; a: string }[];
  
    return (
      <section className="py-12 md:py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <h2 className="font-display text-3xl md:text-4xl font-bold text-white text-center mb-12">
            {t('landing.faq.title')}
          </h2>

        <div className="space-y-4">
          {faqItems.map((item, idx) => {
            const isOpen = openIndex === idx;
            return (
              <div 
                key={idx}
                className={`rounded-2xl border transition-all duration-300 ${
                  isOpen ? 'border-primary/50 bg-primary/5' : 'border-white/10 bg-secondary/30'
                }`}
              >
                <button
                  onClick={() => { setOpenIndex(isOpen ? null : idx); }}
                  className="w-full flex items-center justify-between p-6 text-left"
                >
                  <span className="font-display font-bold text-white md:text-lg">
                    {item.q}
                  </span>
                  <ChevronDown 
                    className={`w-5 h-5 text-text-secondary transition-transform duration-300 ${
                      isOpen ? 'rotate-180 text-primary' : ''
                    }`} 
                  />
                </button>
                <div 
                  className={`overflow-hidden transition-all duration-300 ${
                    isOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
                  }`}
                >
                  <div className="p-6 pt-0 text-text-secondary leading-relaxed md:text-lg">
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
