import { useTranslation } from 'react-i18next';

import { InsightScreen } from '../../shared/components/layout/InsightScreen';

import { WeightTab } from './components/WeightTab';

/**
 * BodyPage component
 *
 * Tracks weight and body composition in a dedicated view.
 */
export default function BodyPage() {
  const { t } = useTranslation();

  return (
    <div data-testid="body-insight-screen">
      <InsightScreen
        title={t('body.weight_title')}
        subtitle={t('body.weight_subtitle')}
        content={<WeightTab />}
      />
    </div>
  );
}
