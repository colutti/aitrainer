import { Calendar, Circle, ClipboardCheck, Pause, Target, WandSparkles, type LucideIcon } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { Skeleton } from '../../../shared/components/ui/Skeleton';
import type { Plan, PlanUpcomingStatus } from '../../../shared/types/plan';

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

function MissionTodayCard({ plan }: { plan: Plan }) {
  const { t } = useTranslation();
  const [sessionTitle, ...exerciseDetails] = plan.mission_today.training;
  const [nutritionHeadline, ...nutritionDetails] = plan.mission_today.nutrition;

  return (
    <div className="rounded-2xl border border-indigo-400/30 bg-indigo-500/10 px-5 py-5">
      <div className="space-y-4">
        <div className="rounded-xl border border-white/10 bg-white/5 px-3 py-3">
        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">{t('plan.cards.training')}</p>
          <p className="mt-1 text-xs font-black text-zinc-200">{sessionTitle ?? t('plan.mission.empty_training')}</p>
        {exerciseDetails.length > 0 ? (
            <ul className="mt-2 space-y-1 border-t border-white/10 pt-2">
            {exerciseDetails.map((item) => (
                  <li key={item} className="text-xs font-semibold text-zinc-400">
                {item}
              </li>
            ))}
          </ul>
        ) : null}
      </div>

        <div className="rounded-xl border border-white/10 bg-white/5 px-3 py-3">
        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">{t('plan.cards.nutrition')}</p>
        {nutritionHeadline ? (
            <p className="mt-1 text-xs font-black text-zinc-200">
            {nutritionHeadline}
          </p>
        ) : (
          <p className="mt-3 text-xs font-semibold text-zinc-400">{t('plan.mission.empty_nutrition')}</p>
        )}
        {nutritionDetails.length > 0 ? (
            <ul className="mt-2 space-y-1 border-t border-white/10 pt-2">
            {nutritionDetails.map((item) => (
                  <li key={item} className="text-xs font-semibold text-zinc-400">
                {item}
              </li>
            ))}
          </ul>
        ) : null}
        {plan.mission_today.coaching ? (
            <p className="mt-2 border-t border-white/10 pt-2 text-xs font-semibold text-zinc-300">{plan.mission_today.coaching}</p>
        ) : null}
        </div>
      </div>
    </div>
  );
}

function UpcomingStatusChip({ status }: { status: PlanUpcomingStatus }) {
  const { t } = useTranslation();

  const statusStyles: Record<PlanUpcomingStatus, { icon: LucideIcon; className: string }> = {
    planned: {
      icon: Circle,
      className: 'border-blue-400/30 bg-blue-400/10 text-blue-200',
    },
    adjusted: {
      icon: WandSparkles,
      className: 'border-amber-400/30 bg-amber-400/10 text-amber-200',
    },
    rest: {
      icon: Pause,
      className: 'border-zinc-400/30 bg-zinc-400/10 text-zinc-300',
    },
  };
  const config = statusStyles[status];
  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 text-[10px] font-black uppercase tracking-[0.2em] ${config.className}`}>
      <Icon size={11} />
      {t(`plan.upcoming.status.${status}`)}
    </span>
  );
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
              {formatDateByLocale(plan.overview.start_date, i18n.language)} - {formatDateByLocale(plan.overview.end_date, i18n.language)}
            </span>
          </div>
          <h2 className="text-2xl md:text-3xl font-black tracking-tight text-white">{plan.overview.title}</h2>
          <p className="max-w-3xl text-base font-semibold leading-relaxed text-zinc-200 md:text-lg">
            {plan.overview.objective_summary}
          </p>
        </div>
      </PremiumCard>

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.25fr)_minmax(0,0.75fr)] gap-6">
        <PremiumCard className="p-6 md:p-8 space-y-6 bg-[color:var(--color-app-surface-raised)] border-white/10">
          <div className="flex items-center gap-2 text-white">
            <Target size={18} className="text-indigo-300" />
            <h3 className="text-lg font-black uppercase tracking-wide">{t('plan.sections.mission_today')}</h3>
          </div>
          <MissionTodayCard plan={plan} />
        </PremiumCard>

        <PremiumCard className="p-6 space-y-3 bg-[color:var(--color-app-surface-raised)] border-white/10">
          <div className="flex items-center gap-2 text-white">
            <ClipboardCheck size={17} className="text-emerald-300" />
            <h3 className="text-sm font-black uppercase tracking-wide">{t('plan.sections.latest_checkpoint')}</h3>
          </div>
          {plan.latest_checkpoint ? (
            <div className="space-y-3">
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">{t('plan.checkpoint.summary')}</p>
                <p className="mt-1 text-xs font-semibold text-zinc-300">{plan.latest_checkpoint.summary}</p>
              </div>
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">{t('plan.checkpoint.ai_assessment')}</p>
                <p className="mt-1 text-xs font-semibold text-zinc-400">{plan.latest_checkpoint.ai_assessment}</p>
              </div>
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">{t('plan.checkpoint.decision')}</p>
                <p className="mt-1 text-xs font-semibold text-zinc-200">{plan.latest_checkpoint.decision}</p>
              </div>
            </div>
          ) : (
            <p className="text-xs font-semibold text-zinc-400">{t('plan.checkpoint.empty')}</p>
          )}
        </PremiumCard>
      </div>

      <PremiumCard className="p-6 md:p-8 space-y-4 bg-[color:var(--color-app-surface-raised)] border-white/10">
        <div className="flex items-center gap-2 text-white">
          <Calendar size={18} className="text-blue-300" />
          <h3 className="text-lg font-black uppercase tracking-wide">{t('plan.sections.upcoming_days')}</h3>
        </div>
        <div className="space-y-3">
          {plan.upcoming_days.length > 0 ? (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
              {plan.upcoming_days.map((day) => (
                <div key={`${day.date}-${day.label}`} className="rounded-2xl border border-white/10 bg-black/20 px-4 py-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-black text-white">{day.label}</p>
                    <UpcomingStatusChip status={day.status} />
                  </div>
                  <div className="mt-3 rounded-xl border border-white/10 bg-white/5 px-3 py-3">
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">{t('plan.cards.training')}</p>
                    <p className="mt-1 text-xs font-black text-zinc-200">{day.training}</p>
                    {day.training_details.length > 0 ? (
                      <ul className="mt-2 space-y-1 border-t border-white/10 pt-2">
                        {day.training_details.map((detail) => (
                          <li key={`${day.date}-${detail}`} className="text-xs font-semibold text-zinc-400">
                            {detail}
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                  <div className="mt-2 rounded-xl border border-white/10 bg-white/5 px-3 py-3">
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">{t('plan.cards.nutrition')}</p>
                    <p className="mt-1 text-xs font-semibold text-zinc-300">{day.nutrition}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs font-semibold text-zinc-400">{t('plan.upcoming.empty')}</p>
          )}
        </div>
      </PremiumCard>
    </div>
  );
}
