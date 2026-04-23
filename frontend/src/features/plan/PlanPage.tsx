import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

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
    <section className="mx-auto w-full max-w-[1600px] space-y-6">
      <div className="space-y-2 px-1">
        <h1 className="text-3xl font-black tracking-tight text-white md:text-4xl">{t('plan.title')}</h1>
        <p className="text-sm font-medium text-zinc-400">{t('plan.subtitle')}</p>
      </div>

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
    </section>
  );
}
