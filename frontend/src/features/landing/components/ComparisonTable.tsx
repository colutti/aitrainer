import { Check, Minus, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const ComparisonTable = () => {
  const { t } = useTranslation();

  const rows = [
    {
      label: t('landing.comparison.rows.price'),
      fityq: t('landing.comparison.values.free'),
      personal: t('landing.comparison.values.personal_price'),
      generic: t('landing.comparison.values.generic_price'),
    },
    {
      label: t('landing.comparison.rows.availability'),
      fityq: t('landing.comparison.values.247'),
      personal: t('landing.comparison.values.scheduled'),
      generic: t('landing.comparison.values.247'),
    },
    {
      label: t('landing.comparison.rows.memory'),
      fityq: <Check className="w-5 h-5 text-[color:var(--color-primary)] mx-auto" />,
      personal: <Minus className="w-5 h-5 text-text-muted mx-auto" />,
      generic: <X className="w-5 h-5 text-text-muted mx-auto" />,
    },
    {
      label: t('landing.comparison.rows.personalization'),
      fityq: t('landing.comparison.values.adaptive_ai'),
      personal: t('landing.comparison.values.high'),
      generic: t('landing.comparison.values.generic'),
    },
    {
      label: t('landing.comparison.rows.integrations'),
      fityq: t('landing.comparison.values.all_apps'),
      personal: t('landing.comparison.values.none'),
      generic: t('landing.comparison.values.limited'),
    },
  ];

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 bg-[color:var(--color-background)] border-t border-[color:var(--color-outline-variant)]">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="font-display text-3xl font-bold text-text-[color:var(--color-primary)] mb-4">
            {t('landing.comparison.title')}
          </h2>
          <p className="text-lg text-text-secondary">
            {t('landing.comparison.subtitle')}
          </p>
        </div>

        <div className="overflow-x-auto rounded-lg border border-[color:var(--color-outline-variant)] shadow-sm">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[color:var(--color-surface-container-low)] border-b border-[color:var(--color-outline-variant)]">
                <th className="p-6 text-xs font-bold text-text-muted uppercase tracking-widest"></th>
                <th className="p-6 text-center">
                  <span className="font-bold text-[color:var(--color-primary)]">
                    {t('landing.comparison.headers.fityq')}
                  </span>
                </th>
                <th className="p-6 text-center text-xs font-bold text-text-muted uppercase tracking-widest">
                  {t('landing.comparison.headers.personal')}
                </th>
                <th className="p-6 text-center text-xs font-bold text-text-muted uppercase tracking-widest">
                  {t('landing.comparison.headers.generic')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {rows.map((row, idx) => (
                <tr 
                  key={idx} 
                  className="bg-[color:var(--color-background)] hover:bg-secondary/50 transition-colors"
                >
                  <td className="p-6 text-sm font-medium text-text-[color:var(--color-primary)]">
                    {row.label}
                  </td>
                  <td className="p-6 text-center text-sm font-bold text-text-[color:var(--color-primary)] bg-[color:var(--color-primary)]/5">
                    {row.fityq}
                  </td>
                  <td className="p-6 text-center text-sm text-text-secondary">
                    {row.personal}
                  </td>
                  <td className="p-6 text-center text-sm text-text-secondary">
                    {row.generic}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
};
