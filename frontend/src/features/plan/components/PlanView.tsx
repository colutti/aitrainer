import { ArrowRight, Calendar, ClipboardCheck, Target } from 'lucide-react';
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

function MissionList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="space-y-3">
      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">{title}</p>
      <ul className="space-y-2">
        {items.map((item) => (
          <li key={`${title}-${item}`} className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm font-semibold text-zinc-200">
            {item}
          </li>
        ))}
      </ul>
    </div>
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
      <PremiumCard className="p-6 md:p-8 space-y-4 bg-[color:var(--color-app-surface-raised)] border-white/10">
        <div className="flex items-center gap-2 text-white">
          <Calendar size={18} className="text-blue-300" />
          <h3 className="text-lg font-black uppercase tracking-wide">{t('plan.sections.time_window')}</h3>
        </div>
        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-[11px] font-black uppercase tracking-[0.15em] text-zinc-200">
          <span>
            {formatDateByLocale(plan.overview.start_date, i18n.language)} - {formatDateByLocale(plan.overview.end_date, i18n.language)}
          </span>
        </div>
      </PremiumCard>

      <PremiumCard className="p-6 md:p-8 bg-[color:var(--color-app-surface-raised)] border-white/10">
        <div className="flex flex-col gap-4">
          <div className="space-y-2">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">{t('plan.sections.overview')}</p>
            <h2 className="text-2xl md:text-3xl font-black tracking-tight text-white">{plan.overview.title}</h2>
            <p className="max-w-2xl text-sm font-medium text-zinc-300">{plan.overview.objective_summary}</p>
          </div>
        </div>
      </PremiumCard>

      <PremiumCard className="p-6 md:p-8 space-y-6 bg-[color:var(--color-app-surface-raised)] border-white/10">
        <div className="flex items-center gap-2 text-white">
          <Target size={18} className="text-indigo-300" />
          <h3 className="text-lg font-black uppercase tracking-wide">{t('plan.sections.mission_today')}</h3>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <MissionList title={t('plan.cards.training')} items={plan.mission_today.training} />
          <MissionList title={t('plan.cards.nutrition')} items={plan.mission_today.nutrition} />
        </div>
      </PremiumCard>

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.25fr)_minmax(0,0.75fr)] gap-6">
        <PremiumCard className="p-6 md:p-8 space-y-4 bg-[color:var(--color-app-surface-raised)] border-white/10">
          <div className="flex items-center gap-2 text-white">
            <Calendar size={18} className="text-blue-300" />
            <h3 className="text-lg font-black uppercase tracking-wide">{t('plan.sections.upcoming_days')}</h3>
          </div>
          <div className="space-y-3">
            {plan.upcoming_days.length > 0 ? (
              plan.upcoming_days.map((day) => (
                <div key={`${day.date}-${day.label}`} className="rounded-2xl border border-white/10 bg-black/20 px-4 py-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-black text-white">{day.label}</p>
                    <span className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">{day.status}</span>
                  </div>
                  <p className="mt-2 text-xs font-semibold text-zinc-300">{day.training}</p>
                  {day.training_details.length > 0 ? (
                    <ul className="mt-2 space-y-1">
                      {day.training_details.map((detail) => (
                        <li key={`${day.date}-${detail}`} className="text-xs font-semibold text-zinc-400">
                          {detail}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                  <p className="mt-1 text-xs font-semibold text-zinc-400">{day.nutrition}</p>
                </div>
              ))
            ) : (
              <p className="text-xs font-semibold text-zinc-400">{t('plan.upcoming.empty')}</p>
            )}
          </div>
        </PremiumCard>

        <div className="space-y-6">
          <PremiumCard className="p-6 space-y-3 bg-[color:var(--color-app-surface-raised)] border-white/10">
            <div className="flex items-center gap-2 text-white">
              <ClipboardCheck size={17} className="text-emerald-300" />
              <h3 className="text-sm font-black uppercase tracking-wide">{t('plan.sections.latest_checkpoint')}</h3>
            </div>
            {plan.latest_checkpoint ? (
              <>
                <p className="text-xs font-semibold text-zinc-300">{plan.latest_checkpoint.summary}</p>
                <p className="text-xs font-semibold text-zinc-400">{plan.latest_checkpoint.ai_assessment}</p>
                <p className="text-xs font-semibold text-zinc-500">{plan.latest_checkpoint.decision}</p>
              </>
            ) : (
              <p className="text-xs font-semibold text-zinc-400">{t('plan.checkpoint.empty')}</p>
            )}
          </PremiumCard>

          <Button type="button" variant="ghost" onClick={onOpenChat} className="w-full justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs font-black uppercase tracking-[0.15em] text-white hover:bg-white/10">
            {t('plan.actions.request_adjustment')}
            <ArrowRight size={14} />
          </Button>
        </div>
      </div>
    </div>
  );
}
