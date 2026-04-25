import {
  Activity,
  AlertCircle,
  Dumbbell,
  Flame,
  Scale,
  Target,
  TrendingDown,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { Skeleton } from '../../../shared/components/ui/Skeleton';
import type {
  DashboardStats,
  PRRecord,
  RecentActivity,
  StreakStats,
  StrengthRadarData,
} from '../../../shared/types/dashboard';
import { cn } from '../../../shared/utils/cn';

import { DashboardMiniChart } from './DashboardMiniChart';
import { DashboardWorkspaceSection } from './DashboardWorkspaceSection';
import { WidgetRecentPRs } from './WidgetRecentPRs';
import { WidgetStrengthRadar } from './WidgetStrengthRadar';
import { WidgetVolumeTrend } from './WidgetVolumeTrend';
import { WidgetWeeklyFrequency } from './WidgetWeeklyFrequency';

export interface DashboardViewProps {
  isLoading: boolean;
  metabolism: DashboardStats['metabolism'];
  body: DashboardStats['body'];
  mergedWeightData: { date: string; weight?: number; trend?: number }[] | null;
  mergedFatData: { date: string; value?: number; trend?: number }[] | null;
  mergedMuscleData: { date: string; value?: number; trend?: number }[] | null;
  recentActivities: RecentActivity[];
  recentPRs: PRRecord[];
  strengthRadar: StrengthRadarData | null;
  volumeTrend: number[];
  weeklyFrequency: boolean[];
  streak: StreakStats | null;
  confidenceLevel: string;
  confidenceColor: string;
  calories: DashboardStats['calories'];
  workouts: DashboardStats['workouts'];
}

export function DashboardView({
  isLoading,
  metabolism,
  body,
  mergedWeightData,
  mergedFatData,
  mergedMuscleData,
  recentActivities,
  recentPRs,
  strengthRadar,
  volumeTrend,
  weeklyFrequency,
  streak,
  confidenceColor,
  confidenceLevel,
  calories,
  workouts,
}: DashboardViewProps) {
  const { t } = useTranslation();

  const renderDiffChip = (
    value: number | null | undefined,
    unit: string,
    label: string,
    positiveClassName: string,
    negativeClassName: string,
    format = (n: number) => n.toFixed(1),
  ) => {
    if (typeof value !== 'number') return null;

    const isPositive = value > 0;
    return (
      <div
        className={cn(
          'inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-black',
          isPositive ? positiveClassName : negativeClassName,
        )}
      >
        {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
        {value > 0 ? '+' : ''}
        {format(Math.abs(value))}
        {unit}
        <span className="ml-1 text-text-muted">{label}</span>
      </div>
    );
  };

  const macroCards = [
    { label: 'Prot', val: metabolism.macro_targets?.protein ?? 0 },
    { label: 'Carb', val: metabolism.macro_targets?.carbs ?? 0 },
    { label: 'Gord', val: metabolism.macro_targets?.fat ?? 0 },
  ];

  if (isLoading) {
    return (
      <div data-testid="dashboard-skeleton" className="space-y-6">
        <Skeleton className="h-24 w-full rounded-[32px] bg-white/5" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-64 rounded-[32px] bg-white/5" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-16" data-testid="dashboard-bento">
      <DashboardWorkspaceSection>
        <section data-testid="dashboard-primary-zone" className="space-y-4">
          <PremiumCard
            withHover={false}
            data-testid="widget-metabolism"
            className="border-white/10 bg-[color:var(--color-app-surface-raised)] p-5"
          >
            <div className="grid gap-5 xl:grid-cols-[minmax(0,1.05fr)_minmax(380px,0.95fr)]">
              <div>
                <div className="mb-2 flex items-center gap-2 text-emerald-400">
                  <Target size={16} />
                  <span className="text-[10px] font-black uppercase tracking-[0.2em]">{t('dashboard.daily_target')}</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-black leading-none text-white">{metabolism.daily_target}</span>
                  <span className="text-xl font-black uppercase text-zinc-400">kcal</span>
                </div>
                <div className="mt-3 flex items-center gap-2">
                  <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-black uppercase tracking-wider text-white">
                    {t(`body.metabolism.goals.${metabolism.goal_type}`)}
                  </span>
                  <span
                    className={cn(
                      'inline-flex h-8 items-center gap-2 rounded-lg border px-3 text-[10px] font-black uppercase tracking-wider',
                      confidenceColor,
                    )}
                  >
                    <Activity size={13} />
                    {confidenceLevel}
                  </span>
                </div>
              </div>

              <div className="space-y-3 rounded-xl border border-white/5 bg-black/20 p-3">
                <div>
                  <div className="mb-1 flex items-center justify-between text-[10px] font-black uppercase tracking-wider">
                    <span className="text-zinc-500">{t('body.metabolism.general_consistency')}</span>
                    <span className="text-emerald-400">{metabolism.consistency_score}%</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-black/40">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-emerald-500 via-cyan-400 to-fuchsia-500"
                      style={{ width: `${String(metabolism.consistency_score)}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="mb-1 flex items-center justify-between text-[10px] font-black uppercase tracking-wider">
                    <span className="text-zinc-500">{t('body.metabolism.caloric_stability')}</span>
                    <span className="text-orange-400">{metabolism.stability_score}%</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-black/40">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-orange-500 to-amber-400"
                      style={{ width: `${String(metabolism.stability_score)}%` }}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2 border-t border-white/5 pt-2">
                  <div>
                    <p className="text-[9px] font-black uppercase tracking-widest text-zinc-500">{t('body.metabolism.tdee_label')}</p>
                    <p className="text-sm font-black text-emerald-400">{metabolism.tdee}</p>
                  </div>
                  <div>
                    <p className="text-[9px] font-black uppercase tracking-widest text-zinc-500">{t('body.metabolism.avg_balance')}</p>
                    <p className={cn('text-sm font-black', metabolism.energy_balance > 0 ? 'text-orange-400' : 'text-emerald-400')}>
                      {metabolism.energy_balance > 0 ? '+' : ''}
                      {metabolism.energy_balance}
                    </p>
                  </div>
                  <div>
                    <p className="text-[9px] font-black uppercase tracking-widest text-zinc-500">{t('body.metabolism.trend_label')}</p>
                    <p className={cn('text-sm font-black', metabolism.weekly_change > 0 ? 'text-orange-400' : 'text-blue-400')}>
                      {metabolism.weekly_change > 0 ? '+' : ''}
                      {metabolism.weekly_change.toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </PremiumCard>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3" data-testid="dashboard-secondary-zone">
            <PremiumCard withHover={false} className="border-white/10 bg-[color:var(--color-app-surface-raised)] p-4">
              <div className="mb-2 flex items-start justify-between">
                <div className="flex items-center gap-2 text-zinc-400">
                  <Scale size={16} className="text-emerald-400" />
                  <span className="text-[10px] font-black uppercase tracking-widest">{t('dashboard.chart.weight')}</span>
                </div>
                <div className="text-[10px] font-black text-zinc-300">7d 15d 30d</div>
              </div>
              <div className="mb-2 flex items-baseline gap-1">
                <span className="text-5xl font-black text-white">{body.weight_current.toFixed(1)}</span>
                <span className="text-lg font-bold text-zinc-500">kg</span>
              </div>
              <div className="mb-2 flex flex-wrap gap-2">
                {renderDiffChip(body.weight_diff, 'kg', '(7d)', 'text-orange-400 bg-orange-400/10', 'text-emerald-400 bg-emerald-400/10')}
                {renderDiffChip(body.weight_diff_15, 'kg', '(15d)', 'text-orange-400 bg-orange-400/10', 'text-emerald-400 bg-emerald-400/10')}
                {renderDiffChip(body.weight_diff_30, 'kg', '(30d)', 'text-orange-400 bg-orange-400/10', 'text-emerald-400 bg-emerald-400/10')}
              </div>
              <DashboardMiniChart data={mergedWeightData} dataKey="weight" color="#22c55e" id="weight" />
            </PremiumCard>

            <PremiumCard withHover={false} data-testid="widget-fat" className="border-white/10 bg-[color:var(--color-app-surface-raised)] p-4">
              <div className="mb-2 flex items-start justify-between">
                <div className="flex items-center gap-2 text-zinc-400">
                  <Flame size={16} className="text-orange-400" />
                  <span className="text-[10px] font-black uppercase tracking-widest">{t('dashboard.chart.fat')}</span>
                </div>
                <div className="text-[10px] font-black text-zinc-300">7d 15d 30d</div>
              </div>
              <div className="mb-2 flex items-baseline gap-1">
                <span className="text-5xl font-black text-white">{typeof body.body_fat_pct === 'number' ? body.body_fat_pct.toFixed(1) : '--'}</span>
                <span className="text-lg font-bold text-zinc-500">%</span>
              </div>
              <div className="mb-2 flex flex-wrap gap-2">
                {renderDiffChip(body.fat_diff, '%', '(7d)', 'text-orange-400 bg-orange-400/10', 'text-emerald-400 bg-emerald-400/10')}
                {renderDiffChip(body.fat_diff_15, '%', '(15d)', 'text-orange-400 bg-orange-400/10', 'text-emerald-400 bg-emerald-400/10')}
                {renderDiffChip(body.fat_diff_30, '%', '(30d)', 'text-orange-400 bg-orange-400/10', 'text-emerald-400 bg-emerald-400/10')}
              </div>
              <DashboardMiniChart data={mergedFatData} dataKey="value" color="#fb923c" id="fat" />
            </PremiumCard>

            <PremiumCard withHover={false} className="border-white/10 bg-[color:var(--color-app-surface-raised)] p-4">
              <div className="mb-2 flex items-start justify-between">
                <div className="flex items-center gap-2 text-zinc-400">
                  <Zap size={16} className="text-blue-400" />
                  <span className="text-[10px] font-black uppercase tracking-widest">{t('dashboard.chart.muscle')}</span>
                </div>
                <div className="text-[10px] font-black text-zinc-300">7d 15d 30d</div>
              </div>
              <div className="mb-2 flex items-baseline gap-1">
                <span className="text-5xl font-black text-white">{typeof body.muscle_mass_kg === 'number' ? body.muscle_mass_kg.toFixed(1) : '--'}</span>
                <span className="text-lg font-bold text-zinc-500">kg</span>
              </div>
              <div className="mb-2 flex flex-wrap gap-2">
                {renderDiffChip(body.muscle_diff_kg, 'kg', '(7d)', 'text-emerald-400 bg-emerald-400/10', 'text-orange-400 bg-orange-400/10')}
                {renderDiffChip(body.muscle_diff_kg_15, 'kg', '(15d)', 'text-emerald-400 bg-emerald-400/10', 'text-orange-400 bg-orange-400/10')}
                {renderDiffChip(body.muscle_diff_kg_30, 'kg', '(30d)', 'text-emerald-400 bg-emerald-400/10', 'text-orange-400 bg-orange-400/10')}
              </div>
              <DashboardMiniChart data={mergedMuscleData} dataKey="value" color="#38bdf8" id="muscle" />
            </PremiumCard>
          </div>

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
            <PremiumCard withHover={false} className="border-white/10 bg-[color:var(--color-app-surface-raised)] p-4 xl:col-span-2">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2 text-orange-400">
                  <Flame size={16} fill="currentColor" />
                  <span className="text-xs font-black uppercase tracking-wider">{t('nutrition.calories')}</span>
                </div>
                <span className="text-3xl font-black text-white">
                  {calories.consumed} <span className="text-lg text-zinc-500">/ {calories.target} kcal</span>
                </span>
              </div>
              <div className="mb-4 flex items-center gap-3">
                <div className="h-3 flex-1 overflow-hidden rounded-full bg-black/40">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-orange-600 to-orange-400"
                    style={{ width: `${String(Math.min(100, calories.percent))}%` }}
                  />
                </div>
                <span className="text-lg font-black text-orange-400">{Math.round(calories.percent)}%</span>
              </div>
              <div className="grid grid-cols-3 gap-2 border-t border-white/5 pt-3">
                {macroCards.map((macro) => (
                  <div key={macro.label} className="rounded-lg border border-white/5 bg-black/20 p-2 text-center">
                    <p className="text-xl font-black text-white">{macro.val}g</p>
                    <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500">{macro.label}</p>
                  </div>
                ))}
              </div>
            </PremiumCard>

            <PremiumCard withHover={false} className="border-white/10 bg-[color:var(--color-app-surface-raised)] p-4">
              <div className="mb-4 flex items-center justify-between">
                <span className="text-xs font-black uppercase tracking-wider text-zinc-300">{t('dashboard.streak')}</span>
                <span className="text-3xl font-black text-white">{streak?.current_weeks ?? 0}</span>
              </div>
              <div className="mb-4 grid grid-cols-2 gap-2">
                <div className="rounded-lg border border-white/5 bg-black/20 p-2 text-center">
                  <p className="text-lg font-black text-white">{streak?.current_weeks ?? 0}</p>
                  <p className="text-[9px] font-black uppercase tracking-widest text-zinc-500">{t('dashboard.streak_w')}</p>
                </div>
                <div className="rounded-lg border border-white/5 bg-black/20 p-2 text-center">
                  <p className="text-lg font-black text-white">{streak?.current_days ?? 0}</p>
                  <p className="text-[9px] font-black uppercase tracking-widest text-zinc-500">{t('dashboard.streak_d')}</p>
                </div>
              </div>
              <div className="mt-4 rounded-lg border border-white/5 bg-black/20 p-2 text-center">
                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500">{t('common.workouts')}</p>
                <p className="text-sm font-black text-white">{workouts.completed}/{workouts.target}</p>
              </div>
            </PremiumCard>
          </div>

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
            <PremiumCard withHover={false} className="border-white/10 bg-[color:var(--color-app-surface-raised)] p-4">
              <div className="mb-3 flex items-center gap-2">
                <span className="text-xs font-black uppercase tracking-wider text-zinc-300">{t('dashboard.recent_prs_title')}</span>
              </div>
              <div className="space-y-2">
                {recentPRs.slice(0, 4).map((pr) => (
                  <div key={pr.id} className="flex items-center justify-between rounded-lg border border-white/5 bg-black/20 px-3 py-2">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-black text-white">{pr.exercise}</p>
                      <p className="text-[10px] uppercase tracking-wider text-zinc-500">
                        {t('dashboard.reps', { count: pr.reps })}
                      </p>
                    </div>
                    <span className="text-sm font-black text-zinc-200">
                      {pr.weight}
                      {t('dashboard.weight_unit')}
                    </span>
                  </div>
                ))}
              </div>
            </PremiumCard>
            <PremiumCard withHover={false} className="border-white/10 bg-[color:var(--color-app-surface-raised)] p-4">
              <WidgetVolumeTrend data={volumeTrend} />
            </PremiumCard>
            <PremiumCard withHover={false} className="border-white/10 bg-[color:var(--color-app-surface-raised)] p-4">
              <WidgetStrengthRadar data={strengthRadar} />
            </PremiumCard>
          </div>
        </section>

        <aside data-testid="dashboard-tertiary-zone" className="space-y-4">
          <PremiumCard withHover={false} className="border-white/10 bg-[color:var(--color-app-surface-raised)] p-4">
            <WidgetRecentPRs prs={recentPRs} />
          </PremiumCard>

          <PremiumCard withHover={false} className="border-white/10 bg-[color:var(--color-app-surface-raised)] p-4">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs font-black uppercase tracking-wider text-zinc-300">{t('dashboard.streak')}</span>
              <span className="text-3xl font-black text-white">{streak?.current_weeks ?? 0}</span>
            </div>
            <WidgetWeeklyFrequency days={weeklyFrequency} />
          </PremiumCard>

          <PremiumCard withHover={false} className="border-white/10 bg-[color:var(--color-app-surface-raised)] p-4">
            <div className="mb-4 flex items-center gap-2 text-zinc-400">
              <Activity size={16} />
              <span className="text-xs font-black uppercase tracking-widest">{t('dashboard.recent_activity')}</span>
            </div>
            <div className="space-y-3">
              {recentActivities.slice(0, 4).map((activity) => (
                <div key={activity.id} className="flex items-start gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-white/5 bg-black/20 text-indigo-400">
                    {activity.type === 'workout' ? <Dumbbell size={14} /> : activity.type === 'nutrition' ? <Flame size={14} /> : <Scale size={14} />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-bold text-white">{activity.title}</p>
                    <p className="truncate text-xs text-zinc-500">{activity.subtitle}</p>
                  </div>
                  <span className="pt-0.5 text-[10px] font-black uppercase text-zinc-600">{activity.date}</span>
                </div>
              ))}
            </div>
          </PremiumCard>
        </aside>
      </DashboardWorkspaceSection>

      <div className="flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-[color:var(--color-app-surface-raised)] p-4">
        <AlertCircle size={14} className="text-zinc-600" />
        <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">{t('body.metabolism.info_desc')}</p>
      </div>

      <PremiumCard withHover={false} className="border-white/10 bg-[color:var(--color-app-surface-raised)] p-5">
        <Link to="/dashboard/plan" data-testid="dashboard-plan-entry" className="group flex items-center justify-between gap-4">
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">{t('dashboard.plan_entry.eyebrow')}</p>
            <p className="mt-1 text-sm font-black text-white">{t('dashboard.plan_entry.title')}</p>
            <p className="mt-1 text-xs font-medium text-zinc-400">{t('dashboard.plan_entry.description')}</p>
          </div>
          <span className="rounded-full border border-white/10 px-3 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-zinc-300 transition-colors group-hover:border-white/25 group-hover:text-white">
            {t('dashboard.plan_entry.cta')}
          </span>
        </Link>
      </PremiumCard>
    </div>
  );
}
