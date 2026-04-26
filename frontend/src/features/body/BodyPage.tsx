import { useTranslation } from 'react-i18next';

import { ViewHeader } from '../../shared/components/ui/premium/ViewHeader';

import { WeightTab } from './components/WeightTab';

/**
 * BodyPage component
 *
 * Tracks weight and body composition in a dedicated view.
 */
export default function BodyPage() {
  const { t } = useTranslation();

  return (
    <section className="mx-auto w-full max-w-[1600px] space-y-8 pb-20">
      <ViewHeader title={t('body.weight_title')} subtitle={t('body.weight_subtitle')} />
      <WeightTab />
    </section>
  );
}
