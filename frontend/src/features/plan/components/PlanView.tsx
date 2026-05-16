import { CalendarDays, Check, Dumbbell } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { Skeleton } from '../../../shared/components/ui/Skeleton';
import type { Plan, PlanRoutine, PlanWeeklyScheduleItem } from '../../../shared/types/plan';
import { cn } from '../../../shared/utils/cn';

interface PlanViewProps {
  plan: Plan | null;
  isLoading: boolean;
  onOpenChat: () => void;
}

interface RingMetric {
  id: string;
  label: string;
  unit: string;
  target: number;
}

const WEEKDAY_ORDER = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function parseIsoDate(value: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]) - 1;
  const day = Number(match[3]);
  const date = new Date(year, month, day);
  if (Number.isNaN(date.getTime())) return null;
  return date;
}

function formatDateByLocale(value: string, locale: string): string {
  const date = parseIsoDate(value);
  if (!date) return value;
  return new Intl.DateTimeFormat(locale, { month: 'short', day: 'numeric' }).format(date);
}

function normalizeDay(value?: string): string {
  if (!value) return '';
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function toWeekdayIndex(isoWeekday: string): number {
  return WEEKDAY_ORDER.indexOf(normalizeDay(isoWeekday));
}

function fromJsDayToIsoWeekday(day: number): string {
  const mapping = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
  return mapping[day] ?? 'monday';
}

function formatWeekdayShort(isoWeekday: string, locale: string): string {
  const idx = toWeekdayIndex(isoWeekday);
  const referenceDate = new Date(2024, 0, idx >= 0 ? idx + 1 : 1);
  return new Intl.DateTimeFormat(locale, { weekday: 'short' }).format(referenceDate);
}

function resolveRoutineForSchedule(
  scheduleItem: PlanWeeklyScheduleItem | undefined,
  routines: PlanRoutine[],
): PlanRoutine | null {
  if (!scheduleItem) return null;
  if (scheduleItem.routine_id) {
    const matchById = routines.find((routine) => normalizeDay(routine.id) === normalizeDay(scheduleItem.routine_id));
    if (matchById) return matchById;
  }

  const focus = normalizeDay(scheduleItem.focus);
  if (focus) {
    const matchByFocus = routines.find((routine) => {
      const name = normalizeDay(routine.name);
      const objective = normalizeDay(routine.objective);
      return name.includes(focus) || objective.includes(focus);
    });
    if (matchByFocus) return matchByFocus;
  }

  return null;
}

function PlanSkeleton() {
  return (
    <div data-testid="plan-skeleton" className="space-y-6 animate-pulse">
      <Skeleton className="h-32 rounded-[var(--radius-lg)] bg-[color:var(--color-surface-container)]" />
      <Skeleton className="h-96 rounded-[var(--radius-lg)] bg-[color:var(--color-surface-container)]" />
      <Skeleton className="h-48 rounded-[var(--radius-lg)] bg-[color:var(--color-surface-container)]" />
    </div>
  );
}

function TimelineHeader({
  title,
  startDate,
  targetDate,
  locale,
}: {
  title: string;
  startDate: string;
  targetDate: string;
  locale: string;
}) {
  const { t } = useTranslation();

  const timeline = useMemo(() => {
    const start = parseIsoDate(startDate);
    const end = parseIsoDate(targetDate);
    const today = new Date();
    if (!start || !end || end < start) {
      return { progress: 0, week: 1, totalWeeks: 1 };
    }

    const totalDays = Math.max(1, Math.ceil((end.getTime() - start.getTime()) / 86400000) + 1);
    const elapsedDays = clamp(Math.ceil((today.getTime() - start.getTime()) / 86400000), 0, totalDays);
    const totalWeeks = Math.max(1, Math.ceil(totalDays / 7));
    const week = clamp(Math.ceil(Math.max(1, elapsedDays) / 7), 1, totalWeeks);
    return {
      progress: clamp(Math.round((elapsedDays / totalDays) * 100), 0, 100),
      week,
      totalWeeks,
    };
  }, [startDate, targetDate]);

  return (
    <PremiumCard className="relative overflow-hidden border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] px-5 py-4 md:px-6 md:py-5">
      <div className="relative space-y-5">
        <div className="flex items-center gap-3 text-text-primary">
          <CalendarDays size={20} className="text-[color:var(--color-primary)]" />
          <h2 className="text-lg md:text-xl font-bold tracking-tight">{title}</h2>
        </div>

        <div className="space-y-3">
          <div className="h-3 w-full rounded-full bg-[color:var(--color-background)]">
            <div
              className="relative h-3 rounded-full"
              style={{
                width: `${String(timeline.progress)}%`,
                backgroundColor: 'var(--color-primary)',
              }}
            >
              <div className="absolute right-[-8px] top-1/2 h-5 w-5 -translate-y-1/2 rounded-full border-2 border-[color:var(--color-primary)] bg-[color:var(--color-surface-container-low)]" />
            </div>
          </div>
          <div className="flex items-center justify-between text-xs font-medium text-text-secondary md:text-sm">
            <p>
              {formatDateByLocale(startDate, locale)} <span className="text-text-muted">({t('plan.labels.start')})</span>
            </p>
            <p className="text-[color:var(--color-primary)]">
              {t('plan.labels.week_of', { week: timeline.week, total: timeline.totalWeeks })}
            </p>
            <p>
              {formatDateByLocale(targetDate, locale)} <span className="text-text-muted">({t('plan.labels.target')})</span>
            </p>
          </div>
        </div>
      </div>
    </PremiumCard>
  );
}

function NutritionTargetCard({ metric }: { metric: RingMetric }) {
  return (
    <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)]">
      <div
        className="px-4 py-2 text-center font-semibold text-[color:var(--color-on-primary)]"
        style={{ backgroundColor: 'var(--color-primary)' }}
      >
        <p className="text-sm md:text-base leading-none">{metric.label}</p>
      </div>
      <div className="px-4 py-5 text-center">
        <p className="text-xl md:text-2xl font-medium leading-none text-text-primary">
          {Math.round(metric.target)}
          <span className="ml-1 text-base md:text-lg">{metric.unit}</span>
        </p>
      </div>
    </div>
  );
}

export function PlanView({ plan, isLoading, onOpenChat }: PlanViewProps) {
  const { t, i18n } = useTranslation();

  const [selectedDay, setSelectedDay] = useState<string>('monday');

  if (isLoading) {
    return <PlanSkeleton />;
  }

  if (!plan) {
    return (
      <PremiumCard className="space-y-4 border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-8 text-center md:p-10">
        <h2 className="text-2xl font-bold tracking-tight text-text-primary">{t('plan.empty.title')}</h2>
        <p className="mx-auto max-w-xl text-sm font-medium text-text-muted">{t('plan.empty.description')}</p>
        <div>
          <Button type="button" onClick={onOpenChat} className="px-6 py-3 font-bold">
            {t('plan.empty.cta')}
          </Button>
        </div>
      </PremiumCard>
    );
  }

  const sortedWeekly = [...plan.training_program.weekly_schedule].sort((a, b) => toWeekdayIndex(a.day) - toWeekdayIndex(b.day));
  const weeklyWithMissingDays = WEEKDAY_ORDER.map((day) => sortedWeekly.find((item) => normalizeDay(item.day) === day) ?? null);
  const todayIsoDay = fromJsDayToIsoWeekday(new Date().getDay());
  const selectedSchedule = weeklyWithMissingDays.find((item) => item && normalizeDay(item.day) === selectedDay) ?? null;
  const selectedRoutine = resolveRoutineForSchedule(selectedSchedule ?? undefined, plan.training_program.routines);
  const isViewingToday = selectedDay === todayIsoDay;

  const metrics = [
    {
      id: 'calories',
      label: t('plan.labels.calories'),
      unit: 'kcal',
      target: plan.nutrition_targets.calories,
    },
    {
      id: 'protein',
      label: t('plan.labels.protein'),
      unit: 'g',
      target: plan.nutrition_targets.protein_g,
    },
    {
      id: 'carbs',
      label: t('plan.labels.carbs'),
      unit: 'g',
      target: plan.nutrition_targets.carbs_g,
    },
    {
      id: 'fat',
      label: t('plan.labels.fat'),
      unit: 'g',
      target: plan.nutrition_targets.fat_g,
    },
  ].filter((item) => item.target > 0) as RingMetric[];

  const successCriteria = [
    t('plan.labels.review_cadence') + ': ' + plan.overview.review_cadence,
    t('plan.labels.active_focus') + ': ' + plan.overview.active_focus,
    ...plan.adherence_notes,
  ].filter((item) => item.trim().length > 0);

  return (
    <div className="space-y-5 pb-20 font-sans" data-testid="plan-view">
      <TimelineHeader
        title={plan.overview.title}
        startDate={plan.overview.start_date}
        targetDate={plan.overview.target_date}
        locale={i18n.language}
      />

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
        <PremiumCard className="space-y-4 border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-5">
          <h3 className="text-sm font-bold uppercase tracking-wide text-text-primary">{t('plan.sections.daily_routine')}</h3>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => {
                setSelectedDay(todayIsoDay);
              }}
              className={cn(
                'rounded-[var(--radius-full)] border px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.05em] transition-colors',
                isViewingToday
                  ? 'border-[color:var(--color-primary)] bg-[color:var(--color-primary)]/15 text-[color:var(--color-primary)]'
                  : 'border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)] text-text-secondary hover:border-[color:var(--color-primary)]/40 hover:text-text-primary'
              )}
            >
              {t('plan.sections.daily_routine')}
            </button>
            <div className="flex min-w-0 flex-1 gap-2 overflow-x-auto pb-1">
              {WEEKDAY_ORDER.map((day) => {
                const isActive = selectedDay === day;
                const label = formatWeekdayShort(day, i18n.language);
                const isToday = day === todayIsoDay;
                return (
                  <button
                    key={day}
                    type="button"
                    onClick={() => {
                      setSelectedDay(day);
                    }}
                    className={cn(
                      'shrink-0 rounded-[var(--radius-md)] border px-3 py-2 text-center text-[11px] md:text-xs font-bold uppercase tracking-[0.05em] transition-colors',
                      isActive
                        ? 'border-[color:var(--color-primary)] bg-[color:var(--color-primary)]/15 text-[color:var(--color-primary)]'
                        : 'border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)] text-text-secondary hover:border-[color:var(--color-primary)]/40 hover:text-text-primary',
                    )}
                    aria-pressed={isActive}
                  >
                    <span>{label}</span>
                    {isToday ? <span className="ml-1 text-[color:var(--color-primary)]">{t('dashboard.week_short')}</span> : null}
                  </button>
                );
              })}
            </div>
          </div>
          <div className="grid grid-cols-1 gap-3 xl:grid-cols-2" data-testid="plan-weekly-exercises">
            {selectedRoutine?.exercises.length ? (
              selectedRoutine.exercises.map((exercise) => (
                <div key={`${selectedDay}-${exercise.name}`} className="flex items-center gap-4 rounded-[var(--radius-lg)] border border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)] p-4">
                  <div className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-[var(--radius-md)] border border-[color:var(--color-outline)] bg-[color:var(--color-surface-container)] text-text-secondary">
                    <Dumbbell size={22} />
                  </div>
                  <div className="space-y-1">
                    <p className="text-base font-semibold text-text-primary md:text-lg">{exercise.name}</p>
                    <div className="flex flex-wrap gap-4 text-xs font-medium text-text-secondary md:text-sm">
                      <span>
                        {t('plan.labels.sets_reps')}: {exercise.sets} x {exercise.reps}
                      </span>
                      <span>
                        {t('plan.labels.rpe')}: {exercise.load_guidance}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="space-y-3 rounded-[var(--radius-lg)] border border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)] p-5 text-sm font-semibold text-text-muted xl:col-span-2">
                <p>{t('plan.labels.rest_day')}</p>
                <Button type="button" variant="secondary" onClick={onOpenChat} className="h-10 rounded-lg px-4 text-xs md:text-sm">
                  {t('plan.empty.cta')}
                </Button>
              </div>
            )}
          </div>
        </PremiumCard>

        <div className="space-y-5">
          <PremiumCard className="space-y-4 border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-5">
            <h3 className="text-sm font-bold uppercase tracking-wide text-text-primary">{t('plan.sections.overview')}</h3>
            <div className="space-y-3 rounded-xl border border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)] p-4">
              <p className="text-xs font-bold uppercase tracking-[0.12em] text-text-muted">{t('plan.labels.primary_goal')}</p>
              <p className="text-lg font-bold text-text-primary md:text-xl">{plan.strategy.rationale}</p>
              <p className="text-sm font-medium text-text-secondary md:text-base">{plan.overview.objective_summary}</p>
            </div>
            <div className="space-y-3 rounded-xl border border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)] p-4">
              <p className="text-xs font-bold uppercase tracking-[0.12em] text-text-muted">{t('plan.labels.success_criteria')}</p>
              <div className="space-y-2">
                {successCriteria.map((criterion) => (
                  <div key={criterion} className="flex items-start gap-2 text-text-secondary">
                    <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-md border border-[color:var(--color-outline)] bg-[color:var(--color-surface-container)] text-text-secondary">
                      <Check size={12} />
                    </span>
                    <p className="text-xs font-medium md:text-sm">{criterion}</p>
                  </div>
                ))}
              </div>
            </div>
          </PremiumCard>

          <PremiumCard className="space-y-5 border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-5">
            <h3 className="text-sm font-bold uppercase tracking-wide text-text-primary">{t('plan.sections.nutrition_strategy')}</h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {metrics.map((metric) => (
                <NutritionTargetCard key={metric.id} metric={metric} />
              ))}
            </div>
          </PremiumCard>

          <PremiumCard className="space-y-3 border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-5">
            <h3 className="text-xs font-bold uppercase tracking-wide text-text-primary">{t('plan.sections.latest_checkpoint')}</h3>
            {plan.latest_checkpoint ? (
              <div className="space-y-2">
                <p className="text-sm font-medium text-text-secondary">{plan.latest_checkpoint.summary}</p>
                <p className="text-xs font-medium text-text-secondary md:text-sm">
                  {t('plan.checkpoint.decision')}: {plan.latest_checkpoint.decision}
                </p>
                <p className="text-xs font-medium text-text-secondary md:text-sm">
                  {t('plan.checkpoint.next_focus')}: {plan.latest_checkpoint.next_focus}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-xs font-semibold text-text-muted">{t('plan.checkpoint.empty')}</p>
                <Button type="button" variant="secondary" onClick={onOpenChat} className="h-10 rounded-lg px-4 text-xs md:text-sm">
                  {t('plan.empty.cta')}
                </Button>
              </div>
            )}
          </PremiumCard>
        </div>
      </div>
    </div>
  );
}
