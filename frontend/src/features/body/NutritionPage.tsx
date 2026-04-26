import { useTranslation } from 'react-i18next';

import { ViewHeader } from '../../shared/components/ui/premium/ViewHeader';

import { NutritionTab } from './components/NutritionTab';

/**
 * NutritionPage component
 *
 * Tracks nutrition logs and macro adherence in a dedicated view.
 */
export default function NutritionPage() {
  const { t } = useTranslation();

  return (
    <section className="mx-auto w-full max-w-[1600px] space-y-8 pb-20">
      <ViewHeader title={t('body.nutrition_title')} subtitle={t('body.nutrition_subtitle')} />
      <NutritionTab />
    </section>
  );
}
