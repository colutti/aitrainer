import { Check, X, Minus } from 'lucide-react';
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
      fityq: <Check className="w-5 h-5 text-emerald-500 mx-auto" />,
      personal: <Minus className="w-5 h-5 text-yellow-500 mx-auto" />,
      generic: <X className="w-5 h-5 text-red-500 mx-auto" />,
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
    <section className="py-12 md:py-16 px-4 sm:px-6 lg:px-8 bg-dark-bg relative overflow-hidden">
      <div className="max-w-5xl mx-auto relative z-10">
        <div className="text-center mb-12">
          <h2 className="font-display text-3xl md:text-4xl font-bold text-white mb-4">
            {t('landing.comparison.title')}
          </h2>
          <p className="text-text-secondary max-w-2xl mx-auto">
            {t('landing.comparison.subtitle')}
          </p>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-white/10 bg-secondary/30 backdrop-blur-xl">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10">
                <th className="p-6 text-sm font-semibold text-text-secondary"></th>
                <th className="p-6 text-center">
                  <span className="font-display font-bold text-primary text-lg">
                    {t('landing.comparison.headers.fityq')}
                  </span>
                </th>
                <th className="p-6 text-center text-sm font-semibold text-white/70">
                  {t('landing.comparison.headers.personal')}
                </th>
                <th className="p-6 text-center text-sm font-semibold text-white/70">
                  {t('landing.comparison.headers.generic')}
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr 
                  key={idx} 
                  className={`border-b border-white/5 last:border-0 hover:bg-white/2 transition-colors`}
                >
                  <td className="p-6 text-sm font-medium text-white">
                    {row.label}
                  </td>
                  <td className="p-6 text-center text-sm font-bold text-white bg-primary/5">
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

      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-primary/10 rounded-full blur-[120px] -z-10" />
    </section>
  );
};
