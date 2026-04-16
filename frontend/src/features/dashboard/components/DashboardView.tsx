import { 
  Flame, 
  Scale, 
  Dumbbell, 
  Zap, 
  Activity, 
  Target, 
  AlertCircle,
  TrendingDown,
  TrendingUp
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { Skeleton } from '../../../shared/components/ui/Skeleton';
import type { 
  RecentActivity, 
  PRRecord,
  StrengthRadarData, 
  StreakStats,
  DashboardStats
} from '../../../shared/types/dashboard';
import { cn } from '../../../shared/utils/cn';

// Sub-widgets
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
          "inline-flex items-center gap-1 text-xs font-black px-2 py-1 rounded-lg",
          isPositive ? positiveClassName : negativeClassName,
        )}
      >
        {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
        {value > 0 ? '+' : ''}{format(Math.abs(value))}{unit}
        <span className="text-text-muted ml-1">{label}</span>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div data-testid="dashboard-skeleton" className="space-y-6">
         <Skeleton className="h-24 w-full rounded-[32px] bg-white/5" />
         <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
           {[1, 2, 3].map(i => <Skeleton key={i} className="h-64 rounded-[32px] bg-white/5" />)}
         </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-20 pr-1" data-testid="dashboard-bento">
      <DashboardWorkspaceSection>
        <section data-testid="dashboard-primary-zone" className="space-y-8">
      {/* --- HUB METABÓLICO PRINCIPAL --- */}
      <PremiumCard withHover={false} data-testid="widget-metabolism" className="p-8 flex flex-col justify-between relative overflow-hidden bg-[color:var(--color-app-surface-raised)] border-white/10">
        <div className="relative z-10 flex justify-between items-start mb-8">
          <div>
            <div className="flex items-center gap-2 text-indigo-400 mb-2">
              <Target size={18} />
              <span className="text-xs font-black uppercase tracking-wider">{t('dashboard.daily_target')}</span>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-6xl font-black tracking-tighter text-white">
                {metabolism.daily_target}
              </span>
              <span className="text-zinc-500 font-bold text-xl ml-1 uppercase">kcal</span>
            </div>
          </div>
          <div className="text-right">
            <span className="text-[10px] font-black text-zinc-500 uppercase tracking-widest block mb-1">Objetivo</span>
            <span className="px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] md:text-xs font-black text-white uppercase tracking-wider whitespace-nowrap">
              {t(`body.metabolism.goals.${metabolism.goal_type}`)}
            </span>
          </div>
        </div>
        
        <div className="relative z-10 mb-8">
          <div className={cn("w-fit px-4 py-2 rounded-xl border text-[10px] font-black uppercase tracking-wider h-[46px] flex items-center gap-3 transition-colors", confidenceColor)}>
            <Activity size={18} />
            <div className="flex flex-col justify-center">
              <span className="opacity-60 leading-none mb-0.5">{t('dashboard.confidence')}</span>
              <span className="text-sm font-black leading-none uppercase tracking-normal">
                {confidenceLevel}
              </span>
            </div>
          </div>
        </div>

        <div className="relative z-10 grid grid-cols-3 gap-4 mb-8 pt-6 border-t border-white/5">
           <div>
              <p className="text-[9px] text-zinc-500 uppercase font-black tracking-widest mb-1">{t('body.metabolism.tdee_label')}</p>
              <p className="text-xl font-black text-emerald-400">{metabolism.tdee}</p>
           </div>
           <div>
              <p className="text-[9px] text-zinc-500 uppercase font-black tracking-widest mb-1">{t('body.metabolism.avg_balance')}</p>
              <p className={cn("text-xl font-black", metabolism.energy_balance > 0 ? "text-orange-400" : "text-emerald-400")}>
                {metabolism.energy_balance > 0 ? '+' : ''}{metabolism.energy_balance}
              </p>
           </div>
           <div>
              <p className="text-[9px] text-zinc-500 uppercase font-black tracking-widest mb-1">{t('body.metabolism.trend_label')}</p>
              <p className={cn("text-xl font-black", metabolism.weekly_change > 0 ? "text-orange-400" : "text-blue-400")}>
                {metabolism.weekly_change > 0 ? '+' : ''}{metabolism.weekly_change.toFixed(2)}
              </p>
           </div>
        </div>

        {/* Consistency */}
        <div className="relative z-10 space-y-4">
           <div className="space-y-1.5">
              <div className="flex justify-between items-center text-[9px] font-black uppercase tracking-wider">
                 <span className="text-zinc-500">{t('body.metabolism.general_consistency')}</span>
                 <span className="text-white">{metabolism.consistency_score}%</span>
              </div>
              <div className="h-1 bg-black/40 rounded-full overflow-hidden">
                <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${String(metabolism.consistency_score)}%` }} />
              </div>
           </div>
           <div className="space-y-1.5">
              <div className="flex justify-between items-center text-[9px] font-black uppercase tracking-wider">
                 <span className="text-zinc-500">{t('body.metabolism.caloric_stability')}</span>
                 <span className="text-white">{metabolism.stability_score}%</span>
              </div>
              <div className="h-1 bg-black/40 rounded-full overflow-hidden">
                <div className="h-full bg-orange-500 rounded-full" style={{ width: `${String(metabolism.stability_score)}%` }} />
              </div>
           </div>
        </div>
      </PremiumCard>

      {/* --- EVOLUTION HIGHLIGHTS --- */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* PESO */}
        <PremiumCard withHover={false} className="p-6 md:p-8 h-auto md:min-h-[18rem] flex flex-col overflow-hidden relative bg-[color:var(--color-app-surface-raised)] border-white/10">
           <div className="relative z-10">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-2 text-zinc-400">
                  <Scale size={18} className="text-emerald-400" />
                  <span className="text-xs font-black uppercase tracking-widest">{t('dashboard.chart.weight')}</span>
                </div>
                <div className={cn("flex items-center gap-1 text-xs font-black px-2 py-1 rounded-lg", body.weight_diff > 0 ? "text-orange-400 bg-orange-400/10" : "text-emerald-400 bg-emerald-400/10")}>
                   {body.weight_diff > 0 ? <TrendingUp size={14}/> : <TrendingDown size={14}/>}
                   {Math.abs(body.weight_diff).toFixed(1)}kg
                </div>
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-5xl font-black tracking-tighter text-white">{body.weight_current.toFixed(1)}</span>
                <span className="text-zinc-500 text-lg font-bold uppercase">kg</span>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {renderDiffChip(body.weight_diff, 'kg', '(7d)', 'text-orange-400 bg-orange-400/10', 'text-emerald-400 bg-emerald-400/10')}
                {renderDiffChip(body.weight_diff_15, 'kg', '(15d)', 'text-orange-400 bg-orange-400/10', 'text-emerald-400 bg-emerald-400/10')}
                {renderDiffChip(body.weight_diff_30, 'kg', '(30d)', 'text-orange-400 bg-orange-400/10', 'text-emerald-400 bg-emerald-400/10')}
              </div>
           </div>
           <DashboardMiniChart data={mergedWeightData} dataKey="weight" color="#10b981" id="weight" />
        </PremiumCard>

        {/* GORDURA */}
        <PremiumCard withHover={false} data-testid="widget-fat" className="p-6 md:p-8 h-auto md:min-h-[18rem] flex flex-col overflow-hidden relative bg-[color:var(--color-app-surface-raised)] border-white/10">
           <div className="relative z-10">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-2 text-zinc-400">
                  <Flame size={18} className="text-orange-400" />
                  <span className="text-xs font-black uppercase tracking-widest">{t('dashboard.chart.fat')}</span>
                </div>
                {typeof body.fat_diff === 'number' && (
                  <div className={cn("flex items-center gap-1 text-xs font-black px-2 py-1 rounded-lg", body.fat_diff > 0 ? "text-orange-400 bg-orange-400/10" : "text-emerald-400 bg-emerald-400/10")}>
                    {body.fat_diff > 0 ? <TrendingUp size={14}/> : <TrendingDown size={14}/>}
                    {Math.abs(body.fat_diff).toFixed(1)}%
                  </div>
                )}
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-5xl font-black tracking-tighter text-white">{typeof body.body_fat_pct === 'number' ? body.body_fat_pct.toFixed(1) : '--'}</span>
                <span className="text-zinc-500 text-lg font-bold uppercase">%</span>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {renderDiffChip(body.fat_diff, '%', '(7d)', 'text-orange-400 bg-orange-400/10', 'text-emerald-400 bg-emerald-400/10')}
                {renderDiffChip(body.fat_diff_15, '%', '(15d)', 'text-orange-400 bg-orange-400/10', 'text-emerald-400 bg-emerald-400/10')}
                {renderDiffChip(body.fat_diff_30, '%', '(30d)', 'text-orange-400 bg-orange-400/10', 'text-emerald-400 bg-emerald-400/10')}
              </div>
           </div>
           <DashboardMiniChart data={mergedFatData} dataKey="value" color="#f97316" id="fat" />
        </PremiumCard>

        {/* MÚSCULO */}
        <PremiumCard withHover={false} className="p-6 md:p-8 h-auto md:min-h-[18rem] flex flex-col overflow-hidden relative bg-[color:var(--color-app-surface-raised)] border-white/10">
           <div className="relative z-10">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-2 text-zinc-400">
                  <Zap size={18} className="text-blue-400" />
                  <span className="text-xs font-black uppercase tracking-widest">{t('dashboard.chart.muscle')}</span>
                </div>
                {typeof body.muscle_diff_kg_15 === 'number' && (
                  <div className={cn(
                    "flex items-center gap-1 text-xs font-black px-2 py-1 rounded-lg",
                    body.muscle_diff_kg_15 > 0 ? "text-emerald-400 bg-emerald-400/10" : "text-red-400 bg-red-400/10"
                  )}>
                     {body.muscle_diff_kg_15 > 0 ? <TrendingUp size={14}/> : <TrendingDown size={14}/>}
                     {Math.abs(body.muscle_diff_kg_15).toFixed(1)}kg
                  </div>
                )}
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-5xl font-black tracking-tighter text-white">
                  {typeof body.muscle_mass_kg === 'number' ? body.muscle_mass_kg.toFixed(1) : '--'}
                </span>
                <span className="text-zinc-500 text-lg font-bold uppercase">kg</span>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {renderDiffChip(body.muscle_diff_kg, 'kg', '(7d)', 'text-emerald-400 bg-emerald-400/10', 'text-orange-400 bg-orange-400/10')}
                {renderDiffChip(body.muscle_diff_kg_15, 'kg', '(15d)', 'text-emerald-400 bg-emerald-400/10', 'text-orange-400 bg-orange-400/10')}
                {renderDiffChip(body.muscle_diff_kg_30, 'kg', '(30d)', 'text-emerald-400 bg-emerald-400/10', 'text-orange-400 bg-orange-400/10')}
              </div>
           </div>
           <DashboardMiniChart data={mergedMuscleData} dataKey="value" color="#3b82f6" id="muscle" />
        </PremiumCard>
      </div>
        </section>
        <aside data-testid="dashboard-tertiary-zone" className="space-y-6">
          <PremiumCard withHover={false} className="p-6 bg-[color:var(--color-app-surface-raised)] border-white/10">
            <WidgetRecentPRs prs={recentPRs} />
          </PremiumCard>
          <PremiumCard withHover={false} className="p-6 bg-[color:var(--color-app-surface-raised)] border-white/10">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-black uppercase tracking-widest text-zinc-500">{t('dashboard.streak')}</span>
              <span className="text-xl font-black text-white">{streak?.current_weeks ?? 0}</span>
            </div>
          </PremiumCard>
          {/* FOOTER INFO */}
          <div className="flex items-center gap-2 p-4 bg-[color:var(--color-app-surface-raised)] border border-white/10 rounded-2xl justify-center">
            <AlertCircle size={14} className="text-zinc-600" />
            <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">
              {t('body.metabolism.info_desc')}
            </p>
          </div>
        </aside>
      </DashboardWorkspaceSection>

      {/* --- GRID SECUNDÁRIO --- */}
      <section data-testid="dashboard-secondary-zone" className="grid grid-cols-1 md:grid-cols-4 gap-6">
        
        {/* CALORIAS CONSUMIDAS */}
        <PremiumCard withHover={false} className="md:col-span-2 p-8 flex flex-col justify-between overflow-hidden bg-[color:var(--color-app-surface-raised)] border-white/10">
           <div>
              <div className="flex items-center gap-2 text-orange-400 mb-4">
                <Flame size={20} fill="currentColor" />
                <span className="text-xs font-black uppercase tracking-wider">{t('nutrition.calories')}</span>
              </div>
              <div className="flex items-baseline gap-2 mb-6">
                <p className="text-6xl font-black text-white leading-none">{calories.consumed}</p>
                <p className="text-zinc-500 font-bold text-xl">/ {calories.target} kcal</p>
              </div>
              
              <div className="flex items-center gap-4 mb-8">
                 <div className="flex-1 h-3 bg-black/40 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-orange-600 to-orange-400 rounded-full shadow-[0_0_15px_rgba(249,115,22,0.4)] transition-all duration-1000" 
                      style={{ width: `${String(Math.min(100, calories.percent))}%` }}
                    />
                 </div>
                 <span className="text-lg font-black text-orange-400">{Math.round(calories.percent)}%</span>
              </div>
           </div>

           {/* Quick Macros */}
           {metabolism.macro_targets && (
             <div className="grid grid-cols-3 gap-4 pt-6 border-t border-white/5">
                {[
                  { label: 'Prot', val: metabolism.macro_targets.protein },
                  { label: 'Carb', val: metabolism.macro_targets.carbs },
                  { label: 'Gord', val: metabolism.macro_targets.fat },
                ].map(m => (
                  <div key={m.label} className="text-center">
                    <p className="text-[10px] font-black text-white">{m.val}g</p>
                    <p className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">{m.label}</p>
                  </div>
                ))}
             </div>
           )}
        </PremiumCard>

        {/* ATIVIDADE RECENTE E FREQUÊNCIA */}
        <div className="md:col-span-2 flex flex-col gap-6">
           <PremiumCard withHover={false} className="p-8 flex-1 bg-[color:var(--color-app-surface-raised)] border-white/10">
              <div className="flex items-center gap-2 text-zinc-400 mb-8 pb-4 border-b border-white/5">
                 <Activity size={18} />
                 <span className="text-xs font-black uppercase tracking-widest">{t('dashboard.recent_activity')}</span>
              </div>
              <div className="space-y-6">
                 {recentActivities.slice(0, 4).map((activity) => (
                    <div key={activity.id} className="flex items-start gap-4">
                      <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-white/5 flex items-center justify-center text-indigo-400 shrink-0">
                         {activity.type === 'workout' ? <Dumbbell size={20} /> :
                          activity.type === 'nutrition' ? <Flame size={20} /> :
                          <Scale size={20} />}
                      </div>
                      <div className="min-w-0 flex-1">
                         <p className="text-white font-bold text-base truncate">{activity.title}</p>
                         <p className="text-zinc-500 text-sm truncate">{activity.subtitle}</p>
                      </div>
                      <div className="text-zinc-600 text-[10px] font-black uppercase pt-1">{activity.date}</div>
                   </div>
                 ))}
              </div>
           </PremiumCard>
           <PremiumCard withHover={false} className="p-6 bg-[color:var(--color-app-surface-raised)] border-white/10">
              <WidgetWeeklyFrequency days={weeklyFrequency} />
           </PremiumCard>
        </div>

        {/* VOLUME, PRs E FORÇA */}
        <div className="md:col-span-2 flex flex-col gap-6">
           <PremiumCard withHover={false} className="p-8 flex-1 bg-[color:var(--color-app-surface-raised)] border-white/10">
              <WidgetVolumeTrend data={volumeTrend} />
           </PremiumCard>
           <PremiumCard withHover={false} className="p-8 flex-1 bg-[color:var(--color-app-surface-raised)] border-white/10">
              <WidgetStrengthRadar data={strengthRadar} />
           </PremiumCard>
        </div>

      </section>
    </div>
  );
}
