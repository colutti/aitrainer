import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

import { InsightScreen } from '../../shared/components/layout/InsightScreen';
import { usePlanStore } from '../../shared/hooks/usePlan';

import { PlanView } from './components/PlanView';

export default function PlanPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { plan, isLoading, fetchPlan } = usePlanStore();

  useEffect(() => {
    void fetchPlan();
  }, [fetchPlan]);

  return (
    <div data-testid="plan-screen">
      <InsightScreen
        title={t('plan.title')}
        subtitle={t('plan.subtitle')}
        content={
          <PlanView
            plan={plan}
            isLoading={isLoading}
            onOpenChat={() => {
              void navigate('/dashboard/chat', {
                state: {
                  draftMessage: t('plan.empty.prefill_message'),
                },
              });
            }}
          />
        }
      />
    </div>
  );
}
