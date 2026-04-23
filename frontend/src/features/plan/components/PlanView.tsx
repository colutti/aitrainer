import { Calendar, ClipboardCheck, Target } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { Skeleton } from '../../../shared/components/ui/Skeleton';
import type { Plan } from '../../../shared/types/plan';

interface PlanViewProps {
  plan: Plan | null;
  isLoading: boolean;
  onOpenChat: () => void;
}

function formatDateByLocale(value: string, locale: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return value;
  const year = Number(match[1]);
  const month = Number(match[2]) - 1;
  const day = Number(match[3]);
  const date = new Date(year, month, day);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(locale).format(date);
}

function PlanSkeleton() {
  return (
    <div data-testid="plan-skeleton" className="space-y-6 animate-pulse">
      <Skeleton className="h-32 rounded-[28px] bg-white/5" />
      <Skeleton className="h-48 rounded-[28px] bg-white/5" />
      <Skeleton className="h-56 rounded-[28px] bg-white/5" />
    </div>
  );
}

export function PlanView({ plan, isLoading, onOpenChat }: PlanViewProps) {
  const { t, i18n } = useTranslation();

  if (isLoading) {
    return <PlanSkeleton />;
  }

  if (!plan) {
    return (
      <PremiumCard className="p-8 md:p-10 text-center space-y-4 bg-[color:var(--color-app-surface-raised)] border-white/10">
        <h2 className="text-2xl font-black tracking-tight text-white">{t('plan.empty.title')}</h2>
        <p className="mx-auto max-w-xl text-sm font-medium text-zinc-400">{t('plan.empty.description')}</p>
        <div>
          <Button type="button" onClick={onOpenChat} className="rounded-full px-6 py-3 font-black">
            {t('plan.empty.cta')}
          </Button>
        </div>
      </PremiumCard>
    );
  }

  return (
    <div className="space-y-6 pb-20" data-testid="plan-view">
      <PremiumCard className="p-6 md:p-8 bg-[color:var(--color-app-surface-raised)] border-white/10">
        <div className="space-y-3">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">{t('plan.sections.overview')}</p>
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-[11px] font-black uppercase tracking-[0.15em] text-zinc-200">
            <Calendar size={14} className="text-blue-300" />
            <span>
              {formatDateByLocale(plan.overview.start_date, i18n.language)} - {formatDateByLocale(plan.overview.target_date, i18n.language)}
            </span>
          </div>
          <h2 className="text-2xl md:text-3xl font-black tracking-tight text-white">{plan.overview.title}</h2>
          <p className="max-w-3xl text-base font-semibold leading-relaxed text-zinc-200 md:text-lg">{plan.overview.objective_summary}</p>
          <p className="text-xs font-semibold text-zinc-400">{t('plan.labels.review_cadence')}: {plan.overview.review_cadence}</p>
          <p className="text-xs font-semibold text-zinc-400">{t('plan.labels.active_focus')}: {plan.overview.active_focus}</p>
        </div>
      </PremiumCard>

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-6">
        <PremiumCard className="p-6 md:p-8 space-y-6 bg-[color:var(--color-app-surface-raised)] border-white/10">
          <div className="flex items-center gap-2 text-white">
            <Target size={18} className="text-indigo-300" />
            <h3 className="text-lg font-black uppercase tracking-wide">{t('plan.sections.strategy')}</h3>
          </div>
          <p className="text-sm font-semibold text-zinc-300">{plan.strategy.rationale}</p>
          <p className="text-xs font-semibold text-zinc-400">{t('plan.labels.adaptation_policy')}: {plan.strategy.adaptation_policy}</p>
          <p className="text-xs font-semibold text-zinc-400">{t('plan.labels.constraints')}: {plan.strategy.constraints.join(', ') || t('plan.labels.none')}</p>
          <p className="text-xs font-semibold text-zinc-400">{t('plan.labels.preferences')}: {plan.strategy.preferences.join(', ') || t('plan.labels.none')}</p>
          <p className="text-xs font-semibold text-zinc-400">{t('plan.labels.current_risks')}: {plan.strategy.current_risks.join(', ') || t('plan.labels.none')}</p>
        </PremiumCard>

        <PremiumCard className="p-6 md:p-8 space-y-6 bg-[color:var(--color-app-surface-raised)] border-white/10">
          <div className="flex items-center gap-2 text-white">
            <ClipboardCheck size={17} className="text-emerald-300" />
            <h3 className="text-lg font-black uppercase tracking-wide">{t('plan.sections.nutrition_targets')}</h3>
          </div>
          <p className="text-sm font-semibold text-zinc-300">{t('plan.labels.calories')}: {plan.nutrition_targets.calories} kcal</p>
          <p className="text-sm font-semibold text-zinc-300">{t('plan.labels.protein')}: {plan.nutrition_targets.protein_g} g</p>
          {plan.nutrition_targets.carbs_g ? <p className="text-sm font-semibold text-zinc-300">{t('plan.labels.carbs')}: {plan.nutrition_targets.carbs_g} g</p> : null}
          {plan.nutrition_targets.fat_g ? <p className="text-sm font-semibold text-zinc-300">{t('plan.labels.fat')}: {plan.nutrition_targets.fat_g} g</p> : null}
          {plan.nutrition_targets.fiber_g ? <p className="text-sm font-semibold text-zinc-300">{t('plan.labels.fiber')}: {plan.nutrition_targets.fiber_g} g</p> : null}
          {plan.adherence_notes.length > 0 ? <p className="text-xs font-semibold text-zinc-400">{plan.adherence_notes.join(' | ')}</p> : null}
        </PremiumCard>
      </div>

      <PremiumCard className="p-6 md:p-8 space-y-4 bg-[color:var(--color-app-surface-raised)] border-white/10">
        <h3 className="text-lg font-black uppercase tracking-wide text-white">{t('plan.sections.training_program')}</h3>
        <p className="text-sm font-semibold text-zinc-300">{t('plan.labels.split')}: {plan.training_program.split_name}</p>
        <p className="text-sm font-semibold text-zinc-300">{t('plan.labels.frequency')}: {plan.training_program.frequency_per_week}</p>
        <p className="text-sm font-semibold text-zinc-300">{t('plan.labels.session_duration')}: {plan.training_program.session_duration_min} min</p>
        <div className="space-y-2">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">{t('plan.sections.weekly_schedule')}</p>
          {plan.training_program.weekly_schedule.map((item, index) => (
            <p key={`${item.day}-${String(index)}`} className="text-xs font-semibold text-zinc-300">
              {item.day}: {item.routine_id ?? item.type} ({item.focus})
            </p>
          ))}
        </div>
        <div className="space-y-3">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">{t('plan.sections.routines')}</p>
          {plan.training_program.routines.map((routine) => (
            <div key={routine.id} className="rounded-xl border border-white/10 bg-white/5 px-3 py-3">
              <p className="text-xs font-black text-zinc-100">{routine.name}</p>
              {routine.objective ? <p className="text-xs font-semibold text-zinc-400">{routine.objective}</p> : null}
              {routine.exercises.map((exercise) => (
                <p key={`${routine.id}-${exercise.name}`} className="text-xs font-semibold text-zinc-300">
                  {exercise.name} - {exercise.sets}x{exercise.reps} ({exercise.load_guidance})
                </p>
              ))}
            </div>
          ))}
        </div>
      </PremiumCard>

      <PremiumCard className="p-6 space-y-3 bg-[color:var(--color-app-surface-raised)] border-white/10">
        <h3 className="text-sm font-black uppercase tracking-wide text-white">{t('plan.sections.latest_checkpoint')}</h3>
        {plan.latest_checkpoint ? (
          <div className="space-y-2">
            <p className="text-xs font-semibold text-zinc-300">{plan.latest_checkpoint.summary}</p>
            <p className="text-xs font-semibold text-zinc-400">{t('plan.checkpoint.decision')}: {plan.latest_checkpoint.decision}</p>
            <p className="text-xs font-semibold text-zinc-400">{t('plan.checkpoint.next_focus')}: {plan.latest_checkpoint.next_focus}</p>
            {plan.latest_checkpoint.evidence.length > 0 ? <p className="text-xs font-semibold text-zinc-400">{plan.latest_checkpoint.evidence.join(' | ')}</p> : null}
          </div>
        ) : (
          <p className="text-xs font-semibold text-zinc-400">{t('plan.checkpoint.empty')}</p>
        )}
      </PremiumCard>
    </div>
  );
}
