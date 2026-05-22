import { AlertTriangle, CalendarDays, CheckCircle2, Dumbbell, Target } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { Skeleton } from '../../../shared/components/ui/Skeleton';
import type { PlanViewModel } from '../../../shared/types/plan';

interface PlanViewProps {
  plan: PlanViewModel | null;
  isLoading: boolean;
  onOpenChat: () => void;
}

function PlanSkeleton() {
  return (
    <div data-testid="plan-skeleton" className="space-y-6 animate-pulse">
      <Skeleton className="h-32 rounded-[var(--radius-lg)] bg-[color:var(--color-surface-container)]" />
      <Skeleton className="h-48 rounded-[var(--radius-lg)] bg-[color:var(--color-surface-container)]" />
      <Skeleton className="h-64 rounded-[var(--radius-lg)] bg-[color:var(--color-surface-container)]" />
    </div>
  );
}

export function PlanView({ plan, isLoading, onOpenChat }: PlanViewProps) {
  const { t } = useTranslation();
  const activePlan = plan?.active_plan ?? null;
  const dayLabels: Record<string, string> = {
    monday: t('plan.days.monday'),
    tuesday: t('plan.days.tuesday'),
    wednesday: t('plan.days.wednesday'),
    thursday: t('plan.days.thursday'),
    friday: t('plan.days.friday'),
    saturday: t('plan.days.saturday'),
    sunday: t('plan.days.sunday'),
  };
  const initialSelectedDay =
    activePlan?.weekly_schedule.find((entry) => entry.is_today)?.day ?? activePlan?.weekly_schedule[0]?.day ?? 'monday';
  const [selectedDayOverride, setSelectedDayOverride] = useState<string | null>(null);
  const selectedDay =
    selectedDayOverride && activePlan?.weekly_schedule.some((entry) => entry.day === selectedDayOverride)
      ? selectedDayOverride
      : initialSelectedDay;

  if (isLoading) {
    return <PlanSkeleton />;
  }

  if (!plan || plan.status === 'NO_PLAN' || plan.status === 'DISCOVERY_IN_PROGRESS') {
    const discovery = plan?.discovery;
    return (
      <div className="space-y-5" data-testid="plan-discovery-view">
        <PremiumCard className="space-y-4 border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-8 text-center md:p-10">
          <h2 className="text-2xl font-bold tracking-tight text-text-primary">{t('plan.empty.title')}</h2>
          <p className="mx-auto max-w-2xl text-sm font-medium text-text-muted">{plan?.generic_response_notice ?? t('plan.empty.description')}</p>
          <Button type="button" onClick={onOpenChat} className="px-6 py-3 font-bold">
            {t('plan.empty.cta')}
          </Button>
        </PremiumCard>

        {discovery ? (
          <PremiumCard className="space-y-4 border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-5">
            <div className="flex items-center gap-3">
              <Target className="text-[color:var(--color-primary)]" size={18} />
              <h3 className="text-sm font-bold uppercase tracking-wide text-text-primary">{t('plan.sections.discovery')}</h3>
            </div>
            <p className="text-sm text-text-secondary">{discovery.next_prompt}</p>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <p className="mb-2 text-xs font-bold uppercase tracking-[0.12em] text-text-muted">{t('plan.labels.collected_fields')}</p>
                <ul className="space-y-1 text-sm text-text-secondary">
                  {discovery.collected_fields.map((field) => {
                    return <li key={field}>{field}</li>;
                  })}
                </ul>
              </div>
              <div>
                <p className="mb-2 text-xs font-bold uppercase tracking-[0.12em] text-text-muted">{t('plan.labels.missing_fields')}</p>
                <ul className="space-y-1 text-sm text-text-secondary">
                  {discovery.missing_fields.map((field) => {
                    return <li key={field}>{field}</li>;
                  })}
                </ul>
              </div>
            </div>
          </PremiumCard>
        ) : null}
      </div>
    );
  }

  if (!activePlan) return null;
  const selectedSchedule =
    activePlan.weekly_schedule.find((entry) => entry.day === selectedDay) ?? activePlan.weekly_schedule[0];

  return (
    <div className="space-y-5 pb-20 font-sans" data-testid="plan-view">
      <PremiumCard className="space-y-4 border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-5">
        <div className="flex items-center gap-3 text-text-primary">
          <CalendarDays size={20} className="text-[color:var(--color-primary)]" />
          <h2 className="text-lg md:text-xl font-bold tracking-tight">{activePlan.title}</h2>
        </div>
        <p className="text-base font-semibold text-text-primary">{activePlan.goal_summary}</p>
      </PremiumCard>

      <PremiumCard className="space-y-4 border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-5">
        <div className="flex items-center gap-3">
          <Target size={18} className="text-[color:var(--color-primary)]" />
          <h3 className="text-sm font-bold uppercase tracking-wide text-text-primary">{t('plan.sections.weekly_schedule')}</h3>
        </div>
        <div className="flex gap-3 overflow-x-auto pb-2" data-testid="plan-weekly-schedule">
          {activePlan.weekly_schedule.map((entry) => (
            <button
              key={entry.day}
              type="button"
              aria-label={dayLabels[entry.day] ?? entry.day}
              aria-pressed={entry.day === selectedDay}
              onClick={() => {
                setSelectedDayOverride(entry.day);
              }}
              className={[
                'min-w-[10rem] flex-shrink-0 rounded-2xl border px-4 py-3 text-left transition-colors',
                entry.day === selectedDay
                  ? 'border-[color:var(--color-primary)] bg-[color:var(--color-background)]'
                  : 'border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)]',
              ].join(' ')}
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs font-bold uppercase tracking-[0.12em] text-text-muted">
                  {dayLabels[entry.day] ?? entry.day}
                </p>
                {entry.is_today ? (
                  <span className="rounded-full bg-[color:var(--color-primary)] px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.14em] text-white">
                    {t('plan.labels.today')}
                  </span>
                ) : null}
              </div>
              <p className="mt-2 text-sm font-semibold text-text-primary">
                {entry.is_rest_day ? t('plan.labels.rest_day_short') : entry.routine_name}
              </p>
              <p className="mt-1 text-xs text-text-secondary">{entry.focus}</p>
            </button>
          ))}
        </div>
      </PremiumCard>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <PremiumCard
          className="space-y-4 border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-5"
          data-testid="plan-daily-routine"
        >
          <div className="flex items-center gap-3">
            <Dumbbell size={18} className="text-[color:var(--color-primary)]" />
            <h3 className="text-sm font-bold uppercase tracking-wide text-text-primary">{t('plan.sections.daily_routine')}</h3>
          </div>
          <p className="text-xs font-bold uppercase tracking-[0.12em] text-text-muted">{dayLabels[selectedSchedule?.day ?? activePlan.today_training.day] ?? selectedSchedule?.day ?? activePlan.today_training.day}</p>
          <p className="text-lg font-semibold text-text-primary">
            {selectedSchedule?.is_rest_day ? t('plan.labels.rest_day') : selectedSchedule?.routine_name}
          </p>
          <p className="text-sm text-text-secondary">{selectedSchedule?.focus ?? activePlan.today_training.focus}</p>
          <div data-testid="plan-weekly-exercises" className="space-y-2">
            {selectedSchedule?.exercise_names.length ? (
              selectedSchedule.exercise_names.map((exercise) => {
                return (
                  <div key={exercise} className="rounded-[var(--radius-lg)] border border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)] px-4 py-3 text-sm text-text-secondary">
                    {exercise}
                  </div>
                );
              })
            ) : (
              <Button type="button" variant="secondary" onClick={onOpenChat} className="h-10 rounded-lg px-4 text-xs md:text-sm">
                {t('plan.empty.cta')}
              </Button>
            )}
          </div>
        </PremiumCard>

        <div className="space-y-5">
          <PremiumCard className="space-y-4 border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-5">
            <h3 className="text-sm font-bold uppercase tracking-wide text-text-primary">{t('plan.sections.overview')}</h3>
            <div className="space-y-2 rounded-xl border border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)] p-4">
              <p className="text-xs font-bold uppercase tracking-[0.12em] text-text-muted">{t('plan.labels.success_criteria')}</p>
              {activePlan.success_metrics.map((metric) => (
                <div key={metric} className="flex items-start gap-2 text-text-secondary">
                  <CheckCircle2 size={14} className="mt-0.5 text-[color:var(--color-primary)]" />
                  <p className="text-sm">{metric}</p>
                </div>
              ))}
            </div>
          </PremiumCard>

          <PremiumCard className="space-y-4 border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-5">
            <h3 className="text-sm font-bold uppercase tracking-wide text-text-primary">{t('plan.sections.nutrition_strategy')}</h3>
            <div className="grid grid-cols-2 gap-3 text-sm text-text-secondary">
              <div className="rounded-xl border border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)] p-4">
                {activePlan.nutrition_targets.calories_kcal} kcal
              </div>
              <div className="rounded-xl border border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)] p-4">
                {activePlan.nutrition_targets.protein_g}g P
              </div>
              <div className="rounded-xl border border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)] p-4">
                {activePlan.nutrition_targets.carbs_g}g C
              </div>
              <div className="rounded-xl border border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)] p-4">
                {activePlan.nutrition_targets.fat_g}g F
              </div>
            </div>
          </PremiumCard>

          <PremiumCard className="space-y-4 border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-5">
            <h3 className="text-sm font-bold uppercase tracking-wide text-text-primary">{t('plan.sections.progress')}</h3>
            {plan.progress ? (
              <div className="space-y-3 text-sm text-text-secondary">
                <p>{plan.progress.training_adherence.details}</p>
                <p>{plan.progress.nutrition_adherence.details}</p>
                <p>{plan.progress.evidence_summary.join(' ')}</p>
              </div>
            ) : (
              <p className="text-sm text-text-muted">{t('plan.progress.empty')}</p>
            )}
            {plan.progress?.conflicts.length ? (
              <div className="space-y-2 rounded-xl border border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)] p-4">
                <div className="flex items-center gap-2">
                  <AlertTriangle size={14} className="text-[color:var(--color-tertiary)]" />
                  <p className="text-xs font-bold uppercase tracking-[0.12em] text-text-muted">{t('plan.sections.conflicts')}</p>
                </div>
                {plan.progress.conflicts.map((conflict) => (
                  <p key={`${conflict.kind}-${conflict.message}`} className="text-sm text-text-secondary">{conflict.message}</p>
                ))}
              </div>
            ) : null}
          </PremiumCard>
        </div>
      </div>
    </div>
  );
}
