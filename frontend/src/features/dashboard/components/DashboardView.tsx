import {
  Activity,
  Dumbbell,
  Flame,
  Scale,
  Target,
  TrendingDown,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

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
          'inline-flex items-center gap-1 rounded-[var(--radius-md)] border px-2 py-1 text-xs font-semibold',
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
        <Skeleton className="h-24 w-full rounded-[var(--radius-lg)] bg-[color:var(--color-surface-container)]" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-64 rounded-[var(--radius-lg)] bg-[color:var(--color-surface-container)]" />
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
            className="border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-5"
          >
            <div className="grid gap-5 xl:grid-cols-[minmax(0,1.05fr)_minmax(380px,0.95fr)]">
              <div>
                <div className="mb-2 flex items-center gap-2 text-[color:var(--color-primary)]">
                  <Target size={16} />
                  <span className="text-[10px] font-semibold uppercase tracking-[0.05em]">{t('dashboard.daily_target')}</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-semibold leading-none text-text-primary">{metabolism.daily_target}</span>
                  <span className="text-xl font-semibold uppercase text-text-secondary">kcal</span>
                </div>
                <div className="mt-3 flex items-center gap-2">
                  <span className="rounded-[var(--radius-full)] border border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container)] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.05em] text-text-primary">
                    {t(`body.metabolism.goals.${metabolism.goal_type}`)}
                  </span>
                  <span
                    className={cn(
                      'inline-flex h-8 items-center gap-2 rounded-[var(--radius-md)] border px-3 text-[10px] font-semibold uppercase tracking-[0.05em]',
                      confidenceColor,
                    )}
                  >
                    <Activity size={13} />
                    {confidenceLevel}
                  </span>
                </div>
              </div>

              <div className="space-y-3 rounded-[var(--radius-lg)] border border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)] p-3">
                <div>
                  <div className="mb-1 flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider">
                    <span className="text-text-muted">{t('body.metabolism.general_consistency')}</span>
                    <span className="text-[color:var(--color-primary)]">{metabolism.consistency_score}%</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-[color:var(--color-background)]">
                    <div
                      className="h-full rounded-full bg-[color:var(--color-primary)]"
                      style={{ width: `${String(metabolism.consistency_score)}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="mb-1 flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider">
                    <span className="text-text-muted">{t('body.metabolism.caloric_stability')}</span>
                    <span className="text-[color:var(--color-secondary)]">{metabolism.stability_score}%</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-[color:var(--color-background)]">
                    <div
                      className="h-full rounded-full bg-[color:var(--color-secondary)]"
                      style={{ width: `${String(metabolism.stability_score)}%` }}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2 border-t border-[color:var(--color-outline-variant)] pt-2">
                  <div>
                    <p className="text-[9px] font-semibold uppercase tracking-[0.05em] text-text-muted">{t('body.metabolism.tdee_label')}</p>
                    <p className="text-sm font-semibold text-[color:var(--color-primary)]">{metabolism.tdee}</p>
                  </div>
                  <div>
                    <p className="text-[9px] font-semibold uppercase tracking-[0.05em] text-text-muted">{t('body.metabolism.avg_balance')}</p>
                    <p className={cn('text-sm font-semibold', metabolism.energy_balance > 0 ? 'text-[color:var(--color-tertiary)]' : 'text-[color:var(--color-primary)]')}>
                      {metabolism.energy_balance > 0 ? '+' : ''}
                      {metabolism.energy_balance}
                    </p>
                  </div>
                  <div>
                    <p className="text-[9px] font-semibold uppercase tracking-[0.05em] text-text-muted">{t('body.metabolism.trend_label')}</p>
                    <p className={cn('text-sm font-semibold', metabolism.weekly_change > 0 ? 'text-[color:var(--color-tertiary)]' : 'text-[color:var(--color-primary)]')}>
                      {metabolism.weekly_change > 0 ? '+' : ''}
                      {metabolism.weekly_change.toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </PremiumCard>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3" data-testid="dashboard-secondary-zone">
            <PremiumCard withHover={false} className="border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-4">
              <div className="mb-2 flex items-start justify-between">
                <div className="flex items-center gap-2 text-text-secondary">
                  <Scale size={16} className="text-[color:var(--color-primary)]" />
                  <span className="text-[10px] font-semibold uppercase tracking-[0.05em]">{t('dashboard.chart.weight')}</span>
                </div>
                <div className="text-[10px] font-semibold text-text-secondary">7d 15d 30d</div>
              </div>
              <div className="mb-2 flex items-baseline gap-1">
                <span className="text-5xl font-semibold text-text-primary">{body.weight_current.toFixed(1)}</span>
                <span className="text-lg font-bold text-text-muted">kg</span>
              </div>
              <div className="mb-2 flex flex-wrap gap-2">
                {renderDiffChip(body.weight_diff, 'kg', '(7d)', 'text-[color:var(--color-tertiary)] bg-orange-400/10', 'text-[color:var(--color-secondary)] bg-emerald-400/10')}
                {renderDiffChip(body.weight_diff_15, 'kg', '(15d)', 'text-[color:var(--color-tertiary)] bg-orange-400/10', 'text-[color:var(--color-secondary)] bg-emerald-400/10')}
                {renderDiffChip(body.weight_diff_30, 'kg', '(30d)', 'text-[color:var(--color-tertiary)] bg-orange-400/10', 'text-[color:var(--color-secondary)] bg-emerald-400/10')}
              </div>
              <DashboardMiniChart data={mergedWeightData} dataKey="weight" color="var(--color-primary)" id="weight" />
            </PremiumCard>

            <PremiumCard withHover={false} data-testid="widget-fat" className="border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-4">
              <div className="mb-2 flex items-start justify-between">
                <div className="flex items-center gap-2 text-text-secondary">
                  <Flame size={16} className="text-[color:var(--color-tertiary)]" />
                  <span className="text-[10px] font-semibold uppercase tracking-[0.05em]">{t('dashboard.chart.fat')}</span>
                </div>
                <div className="text-[10px] font-semibold text-text-secondary">7d 15d 30d</div>
              </div>
              <div className="mb-2 flex items-baseline gap-1">
                <span className="text-5xl font-semibold text-text-primary">{typeof body.body_fat_pct === 'number' ? body.body_fat_pct.toFixed(1) : '--'}</span>
                <span className="text-lg font-bold text-text-muted">%</span>
              </div>
              <div className="mb-2 flex flex-wrap gap-2">
                {renderDiffChip(body.fat_diff, '%', '(7d)', 'text-[color:var(--color-tertiary)] bg-orange-400/10', 'text-[color:var(--color-secondary)] bg-emerald-400/10')}
                {renderDiffChip(body.fat_diff_15, '%', '(15d)', 'text-[color:var(--color-tertiary)] bg-orange-400/10', 'text-[color:var(--color-secondary)] bg-emerald-400/10')}
                {renderDiffChip(body.fat_diff_30, '%', '(30d)', 'text-[color:var(--color-tertiary)] bg-orange-400/10', 'text-[color:var(--color-secondary)] bg-emerald-400/10')}
              </div>
              <DashboardMiniChart data={mergedFatData} dataKey="value" color="var(--color-tertiary)" id="fat" />
            </PremiumCard>

            <PremiumCard withHover={false} className="border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-4">
              <div className="mb-2 flex items-start justify-between">
                <div className="flex items-center gap-2 text-text-secondary">
                  <Zap size={16} className="text-[color:var(--color-primary)]" />
                  <span className="text-[10px] font-semibold uppercase tracking-[0.05em]">{t('dashboard.chart.muscle')}</span>
                </div>
                <div className="text-[10px] font-semibold text-text-secondary">7d 15d 30d</div>
              </div>
              <div className="mb-2 flex items-baseline gap-1">
                <span className="text-5xl font-semibold text-text-primary">{typeof body.muscle_mass_kg === 'number' ? body.muscle_mass_kg.toFixed(1) : '--'}</span>
                <span className="text-lg font-bold text-text-muted">kg</span>
              </div>
              <div className="mb-2 flex flex-wrap gap-2">
                {renderDiffChip(body.muscle_diff_kg, 'kg', '(7d)', 'text-[color:var(--color-secondary)] bg-emerald-400/10', 'text-[color:var(--color-tertiary)] bg-orange-400/10')}
                {renderDiffChip(body.muscle_diff_kg_15, 'kg', '(15d)', 'text-[color:var(--color-secondary)] bg-emerald-400/10', 'text-[color:var(--color-tertiary)] bg-orange-400/10')}
                {renderDiffChip(body.muscle_diff_kg_30, 'kg', '(30d)', 'text-[color:var(--color-secondary)] bg-emerald-400/10', 'text-[color:var(--color-tertiary)] bg-orange-400/10')}
              </div>
              <DashboardMiniChart data={mergedMuscleData} dataKey="value" color="var(--color-primary)" id="muscle" />
            </PremiumCard>
          </div>

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
            <PremiumCard withHover={false} className="border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-4 xl:col-span-2">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2 text-[color:var(--color-tertiary)]">
                  <Flame size={16} fill="currentColor" />
                  <span className="text-xs font-semibold uppercase tracking-[0.05em]">{t('nutrition.calories')}</span>
                </div>
                <span className="text-3xl font-semibold text-text-primary">
                  {calories.consumed} <span className="text-lg text-text-muted">/ {calories.target} kcal</span>
                </span>
              </div>
              <div className="mb-4 flex items-center gap-3">
                <div className="h-3 flex-1 overflow-hidden rounded-full bg-[color:var(--color-background)]">
                  <div
                    className="h-full rounded-full bg-[color:var(--color-tertiary)]"
                    style={{ width: `${String(Math.min(100, calories.percent))}%` }}
                  />
                </div>
                <span className="text-lg font-semibold text-[color:var(--color-tertiary)]">{Math.round(calories.percent)}%</span>
              </div>
              <div className="grid grid-cols-3 gap-2 border-t border-[color:var(--color-outline-variant)] pt-3">
                {macroCards.map((macro) => (
                  <div key={macro.label} className="rounded-lg border border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)] p-2 text-center">
                    <p className="text-xl font-semibold text-text-primary">{macro.val}g</p>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.05em] text-text-muted">{macro.label}</p>
                  </div>
                ))}
              </div>
            </PremiumCard>

          </div>

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            <PremiumCard withHover={false} className="border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-4">
              <WidgetVolumeTrend data={volumeTrend} />
            </PremiumCard>
            <PremiumCard withHover={false} className="border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-4">
              <WidgetStrengthRadar data={strengthRadar} />
            </PremiumCard>
          </div>
        </section>

        <aside data-testid="dashboard-tertiary-zone" className="space-y-4">
          <PremiumCard withHover={false} className="border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-4">
            <WidgetRecentPRs prs={recentPRs} />
          </PremiumCard>

          <PremiumCard withHover={false} className="border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-4">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-text-secondary">{t('dashboard.streak')}</span>
              <span className="text-3xl font-semibold text-text-primary">{streak?.current_weeks ?? 0}</span>
            </div>
            <WidgetWeeklyFrequency days={weeklyFrequency} />
          </PremiumCard>

          <PremiumCard withHover={false} className="border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] p-4">
            <div className="mb-4 flex items-center gap-2 text-text-secondary">
              <Activity size={16} />
              <span className="text-xs font-semibold uppercase tracking-[0.05em]">{t('dashboard.recent_activity')}</span>
            </div>
            <div className="space-y-3">
              {recentActivities.slice(0, 4).map((activity) => (
                <div key={activity.id} className="flex items-start gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)] text-[color:var(--color-primary)]">
                    {activity.type === 'workout' ? <Dumbbell size={14} /> : activity.type === 'nutrition' ? <Flame size={14} /> : <Scale size={14} />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-bold text-text-primary">{activity.title}</p>
                    <p className="truncate text-xs text-text-muted">{activity.subtitle}</p>
                  </div>
                  <span className="pt-0.5 text-[10px] font-semibold uppercase text-text-muted">{activity.date}</span>
                </div>
              ))}
            </div>
          </PremiumCard>
        </aside>
      </DashboardWorkspaceSection>

    </div>
  );
}
