import {
  Scale,
  Flame,
  Dumbbell,
  History,
  Activity,
  Zap,
  Target,
  TrendingDown
} from 'lucide-react';
import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { EmptyState } from '../../shared/components/ui/EmptyState';
import { HelpTooltip } from '../../shared/components/ui/HelpTooltip';
import { StatsCard } from '../../shared/components/ui/StatsCard';
import { useAuthStore } from '../../shared/hooks/useAuth';
import { useDashboardStore } from '../../shared/hooks/useDashboard';
import { useNotificationStore } from '../../shared/hooks/useNotification';
import { cn } from '../../shared/utils/cn';

import { WidgetRecentPRs } from './components/WidgetRecentPRs';
import { WidgetStreak } from './components/WidgetStreak';
import { WidgetStrengthRadar } from './components/WidgetStrengthRadar';
import { WidgetVolumeTrend } from './components/WidgetVolumeTrend';
import { WidgetWeeklyFrequency } from './components/WidgetWeeklyFrequency';

/**
 * DashboardPage component
 * 
 * Main landing page.
 * Hierarchy:
 * 1. Metabolism/TDEE (The "Engine")
 * 2. Body Composition (The "Result")
 * 3. Daily Tracking (The "Action")
 */
export function DashboardPage() {
  const { data, isLoading, fetchData } = useDashboardStore();
  const { userInfo, loadUserInfo } = useAuthStore();
  const { t, i18n } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const notification = useNotificationStore();
  const hasTriggeredPaymentToast = useRef(false);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  useEffect(() => {
    const paymentStatus = searchParams.get('payment');
    if (paymentStatus === 'success' && !hasTriggeredPaymentToast.current) {
      hasTriggeredPaymentToast.current = true;
      void loadUserInfo();
      notification.success(t('landing.subscription.payment_success_message', { defaultValue: 'Pagamento realizado com sucesso! Bem-vindo ao time FityQ.' }));
      
      const newParams = new URLSearchParams(searchParams);
      newParams.delete('payment');
      setSearchParams(newParams, { replace: true });
    } else if (paymentStatus === 'cancelled' && !hasTriggeredPaymentToast.current) {
      hasTriggeredPaymentToast.current = true;
      notification.info(t('landing.subscription.payment_cancelled_message', { defaultValue: 'O processo de pagamento foi interrompido. Você pode tentar novamente quando quiser.' }));
      
      const newParams = new URLSearchParams(searchParams);
      newParams.delete('payment');
      setSearchParams(newParams, { replace: true });
    }
  }, [searchParams, setSearchParams, notification, t, loadUserInfo]);

  if (isLoading && !data) {
    return (
      <div className="space-y-10">
        <div className="h-64 bg-dark-card rounded-xl border border-border w-full" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-dark-card rounded-xl border border-border" />
          ))}
        </div>
      </div>
    );
  }

  const stats = data?.stats ?? {
    metabolism: {
      tdee: 0,
      daily_target: 0,
      confidence: 'none' as const,
      weekly_change: 0,
      energy_balance: 0,
      status: 'maintenance',
      macro_targets: null,
      goal_type: 'maintain' as const,
      consistency_score: 0
    },
    body: {
      weight_current: 0,
      weight_diff: 0,
      weight_diff_15: null,
      weight_diff_30: null,
      weight_trend: 'stable' as const,
      body_fat_pct: null,
      fat_diff: null,
      fat_diff_15: null,
      fat_diff_30: null,
      muscle_mass_pct: null,
      muscle_mass_kg: null,
      muscle_diff: null,
      muscle_diff_15: null,
      muscle_diff_30: null,
      muscle_diff_kg: null,
      muscle_diff_kg_15: null,
      muscle_diff_kg_30: null,
      bmr: null
    },
    calories: { consumed: 0, target: 0, percent: 0 },
    workouts: { completed: 0, target: 0 },
  };

  const { metabolism, body, calories, workouts } = stats;
  const { streak, weightHistory, recentPRs, strengthRadar, volumeTrend, weeklyFrequency } = data ?? {};

  // Helper function to merge weight and trend data
  // weightTrend já vem EMA-suavizado do backend, sem necessidade de recalcular
  const getMergedWeightData = () => {
    if (!data?.weightTrend || !weightHistory) return null;

    const dateMap = new Map<string, Record<string, unknown>>();

    weightHistory.forEach(point => {
      const dateStr = typeof point.date === 'string' ? point.date : String(point.date);
      const dateKey = dateStr.split('T')[0];
      if (dateKey) {
        dateMap.set(dateKey, { date: dateKey, weight: point.weight });
      }
    });

    data.weightTrend.forEach(point => {
      const dateStr = typeof point.date === 'string' ? point.date : String(point.date);
      const dateKey = dateStr.split('T')[0];
      if (dateKey) {
        const existing = dateMap.get(dateKey) ?? { date: dateKey };
        existing.trend = point.value;  // EMA já vem do backend
        dateMap.set(dateKey, existing);
      }
    });

    return Array.from(dateMap.values()).sort((a, b) => {
      const dateA = new Date(String(a.date)).getTime();
      const dateB = new Date(String(b.date)).getTime();
      return dateA - dateB;
    });
  };

  // Helper function for fat trend data (merge raw + EMA)
  const getMergedFatData = () => {
    if (!data?.fatTrend) return null;

    interface FatDataPoint {
      date: string;
      value?: number;
      trend?: number;
    }

    const dateMap = new Map<string, FatDataPoint>();

    // Raw fat history
    if (data.fatHistory) {
      data.fatHistory.forEach((point) => {
        const dateStr = typeof point.date === 'string' ? point.date : String(point.date);
        const dateKey = dateStr.split('T')[0] ?? dateStr;
        if (dateKey && typeof point.value === 'number') {
          dateMap.set(dateKey, { date: dateKey, value: point.value });
        }
      });
    }

    // EMA trend data
    data.fatTrend.forEach((point) => {
      const dateStr = typeof point.date === 'string' ? point.date : String(point.date);
      const dateKey = dateStr.split('T')[0] ?? dateStr;
      if (dateKey && typeof point.value === 'number') {
        const existing = dateMap.get(dateKey) ?? { date: dateKey };
        existing.trend = point.value;  // EMA do backend
        dateMap.set(dateKey, existing);
      }
    });

    return Array.from(dateMap.values()).sort((a, b) => {
      const dateA = new Date(a.date).getTime();
      const dateB = new Date(b.date).getTime();
      return dateA - dateB;
    });
  };

  // Helper function for muscle trend data (merge raw + EMA)
  const getMergedMuscleData = () => {
    if (!data?.muscleTrend) return null;

    interface MuscleDataPoint {
      date: string;
      value?: number;
      trend?: number;
    }

    const dateMap = new Map<string, MuscleDataPoint>();

    // Raw muscle history
    if (data.muscleHistory) {
      data.muscleHistory.forEach((point) => {
        const dateStr = typeof point.date === 'string' ? point.date : String(point.date);
        const dateKey = dateStr.split('T')[0] ?? dateStr;
        if (dateKey && typeof point.value === 'number') {
          dateMap.set(dateKey, { date: dateKey, value: point.value });
        }
      });
    }

    // EMA trend data
    data.muscleTrend.forEach((point) => {
      const dateStr = typeof point.date === 'string' ? point.date : String(point.date);
      const dateKey = dateStr.split('T')[0] ?? dateStr;
      if (dateKey && typeof point.value === 'number') {
        const existing = dateMap.get(dateKey) ?? { date: dateKey };
        existing.trend = point.value;  // EMA do backend
        dateMap.set(dateKey, existing);
      }
    });

    return Array.from(dateMap.values()).sort((a, b) => {
      const dateA = new Date(a.date).getTime();
      const dateB = new Date(b.date).getTime();
      return dateA - dateB;
    });
  };

  const mergedWeightData = getMergedWeightData();
  const mergedFatData = getMergedFatData();
  const mergedMuscleData = getMergedMuscleData();

  const confidenceColor = {
    'high': 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
    'medium': 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
    'low': 'text-orange-400 bg-orange-400/10 border-orange-400/20',
    'none': 'text-text-muted bg-white/5 border-white/10'
  }[metabolism.confidence] ?? 'text-text-muted';

  const confidenceLevel = (metabolism.confidence === 'none' || !metabolism.confidence)
    ? t('dashboard.confidence_level.none')
    : t(`dashboard.confidence_level.${metabolism.confidence.toLowerCase()}`, { defaultValue: t('dashboard.confidence_level.unknown') });

  return (
    <div className="space-y-10">
      
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className="text-3xl font-black text-text-primary tracking-tight">
            {t('dashboard.greeting', { name: userInfo?.name ?? t('common.athlete', { defaultValue: 'Athlete' }) })}
          </h1>
          <p className="text-text-secondary mt-2 text-sm font-medium">
            {t('dashboard.summary_subtitle')}
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {streak && (
            <WidgetStreak currentWeeks={streak.current_weeks} currentDays={streak.current_days} />
          )}
          <div className={cn("px-4 py-2 rounded-lg border text-[10px] font-black uppercase tracking-wider h-[44px] flex items-center gap-3 transition-colors", confidenceColor)}>
            <Activity size={18} />
            <div className="flex flex-col justify-center">
              <span className="opacity-60 leading-none mb-1">{t('dashboard.confidence')}</span>
              <span className="text-sm font-black leading-none uppercase tracking-normal">
                {confidenceLevel}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      {/* 2. PRIORITY 1: METABOLISM & TDEE (The Engine) */}
      <div id="widget-metabolism" className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Main Target Card */}
        <div className="xl:col-span-2 bg-dark-bg border border-border rounded-xl p-6 md:p-8 relative overflow-hidden">
          <div className="relative z-10 flex flex-col xl:flex-row justify-between gap-8 h-full">
            <div className="flex-1 flex flex-col items-center xl:items-start text-center xl:text-left space-y-8 w-full min-w-0">
              <div className="flex flex-col md:flex-row items-center gap-4">
                <div className="p-3 rounded-xl bg-gradient-start/10 text-gradient-start shrink-0">
                  <Target size={24} />
                </div>
                <div className="min-w-0">
                  <h2 className="text-lg font-black text-text-primary leading-tight truncate">{t('dashboard.daily_target')}</h2>
                  <p className="text-sm text-text-muted font-medium truncate">{t('dashboard.focus', { goal: t(`dashboard.goals.${metabolism.goal_type}`) })}</p>
                </div>
              </div>
              
              <div className="flex flex-col items-center xl:items-start">
                <div className="flex items-baseline gap-2 flex-wrap justify-center xl:justify-start">
                  <span className="text-6xl md:text-7xl font-black text-white tracking-tighter leading-none">
                    {metabolism.daily_target}
                  </span>
                  <span className="text-text-muted text-lg font-black uppercase tracking-wider">kcal</span>
                </div>
              </div>

               <div className="w-full grid grid-cols-2 xl:flex xl:gap-12 pt-8 border-t border-white/5 px-4 xl:px-0">
                  <div className="space-y-1.5 min-w-0">
                     <div className="flex items-center gap-1.5 text-text-muted">
                        <p className="text-[11px] uppercase font-black tracking-wider whitespace-nowrap">{t('body.metabolism.tdee_label')}</p>
                        <HelpTooltip content={t('body.metabolism.info_desc')} />
                     </div>
                     <p className="text-2xl font-black text-emerald-400 flex items-center gap-2 truncate">
                        <Zap size={18} fill="currentColor" /> {metabolism.tdee}
                     </p>
                  </div>
                  
                  <div className="space-y-1.5 border-l border-white/5 pl-8 xl:pl-12 min-w-0">
                     <div className="flex items-center gap-1.5 text-text-muted">
                        <p className="text-[11px] uppercase font-black tracking-wider whitespace-nowrap">{t('body.metabolism.trend_label')}</p>
                        <HelpTooltip content={t('dashboard.trend_disclaimer')} />
                     </div>
                     <p className={cn("text-2xl font-black flex items-center gap-2 truncate", metabolism.weekly_change > 0 ? "text-orange-400" : "text-blue-400")}>
                        <TrendingDown size={20} className={metabolism.weekly_change > 0 ? "rotate-180" : undefined} />
                        {Math.abs(metabolism.weekly_change).toFixed(2)} <span className="text-xs font-black uppercase">kg</span>
                     </p>
                  </div>
               </div>
              
              <p className="text-[10px] text-text-muted italic mt-4 opacity-70 max-w-sm hidden xl:block">
                {t('dashboard.trend_disclaimer')}
              </p>
            </div>

            {/* Macro Preview (if available) */}
            {metabolism.macro_targets && (
              <div className="w-full xl:w-80 bg-white/5 rounded-xl p-5 border border-white/5 backdrop-blur-sm">
                <h3 className="text-xs font-black text-text-muted mb-4 uppercase tracking-widest text-center xl:text-left">{t('dashboard.suggested_macros')}</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center gap-4">
                     <span className="text-sm font-black text-text-primary uppercase tracking-wider truncate">{t('dashboard.protein')}</span>
                     <span className="font-black text-emerald-400 shrink-0">{metabolism.macro_targets.protein}g</span>
                  </div>
                  <div className="w-full bg-white/10 h-2 rounded overflow-hidden border border-white/5">
                     <div className="h-full bg-emerald-500 w-full" />
                  </div>
                  
                  <div className="flex justify-between items-center gap-4">
                     <span className="text-sm font-black text-text-primary uppercase tracking-wider truncate">{t('dashboard.fat')}</span>
                     <span className="font-black text-yellow-500 shrink-0">{metabolism.macro_targets.fat}g</span>
                  </div>
                   <div className="w-full bg-white/10 h-2 rounded overflow-hidden border border-white/5">
                     <div className="h-full bg-yellow-500 w-full" />
                  </div>

                  <div className="flex justify-between items-center gap-4">
                     <span className="text-sm font-black text-text-primary uppercase tracking-wider truncate">{t('dashboard.carbs')}</span>
                     <span className="font-black text-blue-400 shrink-0">{metabolism.macro_targets.carbs}g</span>
                  </div>
                  <div className="w-full bg-white/10 h-2 rounded overflow-hidden border border-white/5">
                     <div className="h-full bg-blue-500 w-full" />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Consistency Score */}
        <div className="bg-dark-bg border border-border rounded-xl p-6 flex flex-col justify-center items-center text-center space-y-4">
             <div className="relative w-32 h-32 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90">
                  <circle cx="64" cy="64" r="56" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-white/5" />
                  <circle cx="64" cy="64" r="56" stroke="currentColor" strokeWidth="8" fill="transparent" 
                          strokeDasharray={351} strokeDashoffset={351 - (351 * metabolism.consistency_score) / 100}
                          className="text-primary transition-all duration-1000" />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center flex-col">
                   <span className="text-3xl font-black">{metabolism.consistency_score}%</span>
                </div>
             </div>
             <div>
               <h3 className="font-black text-base text-text-primary uppercase tracking-widest">{t('dashboard.consistency')}</h3>
               <p className="text-xs text-text-muted mt-1 font-medium">{t('dashboard.consistency_subtitle')}</p>
             </div>
        </div>
      </div>

      {/* 3. PRIORITY 2: BODY COMPOSITION (The Result) */}
      <div id="widget-weight-chart" className="space-y-4 pt-4">
        <div className="flex items-center gap-2.5">
          <Activity className="text-primary" size={20} />
          <h2 className="text-xl font-black text-text-primary tracking-tight">{t('dashboard.body_composition')}</h2>
        </div>

        {/* Composition Charts - Grid: Weight + Fat on first row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Weight Card */}
          <div className="bg-dark-bg border border-border rounded-xl p-6 relative overflow-hidden transition-colors hover:border-white/20">
            {(!weightHistory || weightHistory.length === 0) ? (
              <EmptyState 
                title={t('dashboard.empty_states.weight_title')}
                description={t('dashboard.empty_states.weight_desc')}
                icon={Scale}
                actionLabel={t('dashboard.empty_states.action_weight')}
                onAction={() => window.location.href = '/body?action=log-weight'}
                className="h-full border-0 bg-transparent"
              />
            ) : (
              <div className="relative z-10 flex flex-col h-full">
                <div className="mb-4">
                  <p className="text-text-secondary text-sm font-medium mb-1">{t('dashboard.current_weight')}</p>
                  <h3 className="text-3xl font-black text-text-primary tracking-tight flex items-center gap-2">
                    {body.weight_current.toFixed(2)} <span className="text-lg text-text-muted">kg</span>
                    <div className="w-8 h-8 rounded bg-emerald-500/10 text-emerald-500 flex items-center justify-center border border-emerald-500/10">
                      <Scale size={16} />
                    </div>
                  </h3>
                  <div className="flex flex-wrap items-center gap-2 mt-2 text-[10px]">
                    <span className={cn(
                      "font-black px-2 py-0.5 rounded-sm uppercase tracking-wider",
                      body.weight_diff > 0 ? 'bg-orange-500/10 text-orange-500' : 'bg-emerald-500/10 text-emerald-500'
                    )}>
                      {body.weight_diff > 0 ? '+' : ''}{body.weight_diff.toFixed(2)} kg <span className="opacity-50 ml-1">(7d)</span>
                    </span>
                    {body.weight_diff_15 !== undefined && body.weight_diff_15 !== null && (
                      <span className={cn(
                        "font-black px-2 py-0.5 rounded-sm uppercase tracking-wider",
                        body.weight_diff_15 > 0 ? 'bg-orange-500/10 text-orange-500' : 'bg-emerald-500/10 text-emerald-500'
                      )}>
                        {body.weight_diff_15 > 0 ? '+' : ''}{body.weight_diff_15.toFixed(2)} kg <span className="opacity-50 ml-1">(15d)</span>
                      </span>
                    )}
                    {body.weight_diff_30 !== undefined && body.weight_diff_30 !== null && (
                      <span className={cn(
                        "font-black px-2 py-0.5 rounded-sm uppercase tracking-wider",
                        body.weight_diff_30 > 0 ? 'bg-orange-500/10 text-orange-500' : 'bg-emerald-500/10 text-emerald-500'
                      )}>
                        {body.weight_diff_30 > 0 ? '+' : ''}{body.weight_diff_30.toFixed(2)} kg <span className="opacity-50 ml-1">(30d)</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Weight chart with two lines */}
                {mergedWeightData && (
                  <div className="flex-1 min-h-[120px] -mx-2 -mb-2">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={mergedWeightData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                        <XAxis dataKey="date" hide />
                        <YAxis hide domain={['dataMin - 0.5', 'dataMax + 0.5']} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#09090b',
                            borderColor: '#27272a',
                            borderRadius: '4px',
                            color: '#fafafa',
                            fontSize: '12px',
                            padding: '8px',
                            boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
                          }}
                          // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
                          formatter={((value: number, _name: string, props: { dataKey: string }) => {
                            const dataKey = props.dataKey;
                            if (dataKey === 'trend') return [value.toFixed(2), t('dashboard.chart.trend')];
                            return [value.toFixed(2), t('dashboard.chart.weight')];
                          }) as any} // eslint-disable-line @typescript-eslint/no-explicit-any
                          labelFormatter={(label) => {
                            const date = new Date(label as string);
                            return isNaN(date.getTime()) ? String(label) : date.toLocaleDateString(i18n.language, { day: '2-digit', month: '2-digit' });
                          }}
                        />
                        {/* Peso Real - linha mais grossa azul (destaque) */}
                        <Line
                          type="monotone"
                          dataKey="weight"
                          stroke="#60a5fa"
                          strokeWidth={2.5}
                          dot={false}
                          isAnimationActive={false}
                          name={t('dashboard.chart.weight')}
                        />
                        {/* Tendência EMA (backend) - linha fina verde */}
                        <Line
                          type="monotone"
                          dataKey="trend"
                          stroke="#10b981"
                          strokeWidth={1}
                          dot={false}
                          isAnimationActive={false}
                          name={t('dashboard.chart.trend')}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Fat Trend */}
          {((data?.fatTrend?.length ?? 0) > 0 || body.body_fat_pct !== null) && (
            <div className="bg-dark-bg border border-border rounded-xl p-6 relative overflow-hidden transition-colors hover:border-white/20">
              <div className="relative z-10 flex flex-col h-full">
                <div className="mb-4">
                  <p className="text-text-secondary text-sm font-medium mb-1">{t('dashboard.body_fat')}</p>
                  <h3 className="text-3xl font-bold text-text-primary tracking-tight flex items-center gap-2">
                    {body.body_fat_pct?.toFixed(1) ?? '--'} <span className="text-lg text-text-muted">%</span>
                    <div className="w-8 h-8 rounded-lg bg-orange-500/10 text-orange-500 flex items-center justify-center">
                      <Flame size={16} />
                    </div>
                  </h3>
                  <div className="flex flex-wrap items-center gap-2 mt-2 text-[10px]">
                    {body.fat_diff !== undefined && body.fat_diff !== null && (
                      <span className={cn(
                        "font-black px-2 py-0.5 rounded-sm uppercase tracking-wider",
                        body.fat_diff > 0 ? 'bg-orange-500/10 text-orange-500' : 'bg-emerald-500/10 text-emerald-500'
                      )}>
                        {body.fat_diff > 0 ? '+' : ''}{body.fat_diff.toFixed(1)} % <span className="text-text-muted ml-1 opacity-50">(7d)</span>
                      </span>
                    )}
                    {body.fat_diff_15 !== undefined && body.fat_diff_15 !== null && (
                      <span className={cn(
                        "font-black px-2 py-0.5 rounded-sm uppercase tracking-wider",
                        body.fat_diff_15 > 0 ? 'bg-orange-500/10 text-orange-500' : 'bg-emerald-500/10 text-emerald-500'
                      )}>
                        {body.fat_diff_15 > 0 ? '+' : ''}{body.fat_diff_15.toFixed(1)} % <span className="text-text-muted ml-1 opacity-50">(15d)</span>
                      </span>
                    )}
                    {body.fat_diff_30 !== undefined && body.fat_diff_30 !== null && (
                      <span className={cn(
                        "font-black px-2 py-0.5 rounded-sm uppercase tracking-wider",
                        body.fat_diff_30 > 0 ? 'bg-orange-500/10 text-orange-500' : 'bg-emerald-500/10 text-emerald-500'
                      )}>
                        {body.fat_diff_30 > 0 ? '+' : ''}{body.fat_diff_30.toFixed(1)} % <span className="text-text-muted ml-1 opacity-50">(30d)</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Fat chart */}
                {mergedFatData && mergedFatData.length > 0 && (
                  <div className="flex-1 min-h-[120px] -mx-2 -mb-2">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={mergedFatData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                        <XAxis dataKey="date" hide />
                        <YAxis hide domain={['dataMin - 1', 'dataMax + 1']} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#09090b',
                            borderColor: '#27272a',
                            borderRadius: '4px',
                            color: '#fafafa',
                            fontSize: '12px',
                            padding: '8px',
                            boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
                          }}
                          formatter={(value: number, name: string) => [value.toFixed(1) + '%', name]}
                          labelFormatter={(label) => {
                            const date = new Date(label as string);
                            return isNaN(date.getTime()) ? String(label) : date.toLocaleDateString(i18n.language, { day: '2-digit', month: '2-digit' });
                          }}
                        />
                        <Line
                          type="monotone"
                          dataKey="value"
                          stroke="#f97316"
                          strokeWidth={2.5}
                          dot={false}
                          isAnimationActive={false}
                          name={t('dashboard.chart.fat')}
                        />
                        <Line
                          type="monotone"
                          dataKey="trend"
                          stroke="#10b981"
                          strokeWidth={1}
                          dot={false}
                          isAnimationActive={false}
                          name={t('dashboard.chart.trend')}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Composition Charts - Row 2: Muscle + BMR */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Muscle Trend */}
          {((data?.muscleTrend?.length ?? 0) > 0 || body.muscle_mass_kg !== null) && (
            <div className="bg-dark-bg border border-border rounded-xl p-6 relative overflow-hidden transition-colors hover:border-white/20">
              <div className="relative z-10 flex flex-col h-full">
                <div className="mb-4">
                  <p className="text-text-secondary text-sm font-medium mb-1">{t('dashboard.muscle_mass')}</p>
                  <h3 className="text-3xl font-black text-text-primary tracking-tight flex items-center gap-2">
                    {body.muscle_mass_kg?.toFixed(1) ?? '--'} <span className="text-lg text-text-muted">kg</span>
                    <div className="w-8 h-8 rounded bg-blue-500/10 text-blue-500 flex items-center justify-center border border-blue-500/10">
                      <Dumbbell size={16} />
                    </div>
                  </h3>
                  <div className="flex flex-wrap items-center gap-2 mt-2 text-[10px]">
                    {body.muscle_diff_kg !== undefined && body.muscle_diff_kg !== null && (
                      <span className={cn(
                        "font-black px-2 py-0.5 rounded-sm uppercase tracking-wider",
                        body.muscle_diff_kg > 0 ? 'bg-emerald-500/10 text-emerald-500' : 'bg-orange-500/10 text-orange-500'
                      )}>
                        {body.muscle_diff_kg > 0 ? '+' : ''}{body.muscle_diff_kg.toFixed(1)} kg <span className="opacity-50 ml-1">(7d)</span>
                      </span>
                    )}
                    {body.muscle_diff_kg_15 !== undefined && body.muscle_diff_kg_15 !== null && (
                      <span className={cn(
                        "font-black px-2 py-0.5 rounded-sm uppercase tracking-wider",
                        body.muscle_diff_kg_15 > 0 ? 'bg-emerald-500/10 text-emerald-500' : 'bg-orange-500/10 text-orange-500'
                      )}>
                        {body.muscle_diff_kg_15 > 0 ? '+' : ''}{body.muscle_diff_kg_15.toFixed(1)} kg <span className="opacity-50 ml-1">(15d)</span>
                      </span>
                    )}
                    {body.muscle_diff_kg_30 !== undefined && body.muscle_diff_kg_30 !== null && (
                      <span className={cn(
                        "font-black px-2 py-0.5 rounded-sm uppercase tracking-wider",
                        body.muscle_diff_kg_30 > 0 ? 'bg-emerald-500/10 text-emerald-500' : 'bg-orange-500/10 text-orange-500'
                      )}>
                        {body.muscle_diff_kg_30 > 0 ? '+' : ''}{body.muscle_diff_kg_30.toFixed(1)} kg <span className="opacity-50 ml-1">(30d)</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Muscle chart */}
                {mergedMuscleData && mergedMuscleData.length > 0 && (
                  <div className="flex-1 min-h-[120px] -mx-2 -mb-2">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={mergedMuscleData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                        <XAxis dataKey="date" hide />
                        <YAxis hide domain={['dataMin - 0.5', 'dataMax + 0.5']} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#09090b',
                            borderColor: '#27272a',
                            borderRadius: '4px',
                            color: '#fafafa',
                            fontSize: '11px',
                            padding: '6px'
                          }}
                          formatter={(value: number, name: string) => [value.toFixed(1) + 'kg', name]}
                          labelFormatter={(label) => {
                            const date = new Date(label as string);
                            return isNaN(date.getTime()) ? String(label) : date.toLocaleDateString(i18n.language, { day: '2-digit', month: '2-digit' });
                          }}
                        />
                      {/* Músculo Real - linha mais grossa azul (destaque) */}
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#3b82f6"
                        strokeWidth={2.5}
                        dot={false}
                        isAnimationActive={false}
                        name={t('dashboard.chart.muscle')}
                      />
                      {/* Tendência EMA (backend) - linha fina verde */}
                      <Line
                        type="monotone"
                        dataKey="trend"
                        stroke="#10b981"
                        strokeWidth={1}
                        dot={false}
                        isAnimationActive={false}
                        name={t('dashboard.chart.trend')}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>
        )}
        </div>
      </div>

      {/* 4. PRIORITY 3: DAILY TRACKING (The Action) */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 pt-4">
         <div id="widget-activity-list" className="xl:col-span-2 space-y-4">
            <div className="flex items-center gap-2.5">
              <History className="text-primary" size={20} />
              <h2 className="text-xl font-black text-text-primary tracking-tight">{t('dashboard.recent_activity')}</h2>
            </div>
            <div className="bg-dark-bg border border-border rounded-xl overflow-hidden min-h-[200px]">
            {data?.recentActivities.length ? (
              <div className="divide-y divide-border">
                {data.recentActivities.map((activity) => (
                  <div key={activity.id} className="p-4 flex items-center gap-4 hover:bg-white/5 transition-colors group">                    <div className="w-10 h-10 rounded bg-dark-bg border border-border flex items-center justify-center text-text-muted group-hover:text-primary transition-colors">
                      {activity.type === 'workout' ? <Dumbbell size={20} /> :
                       activity.type === 'nutrition' ? <Flame size={20} /> :
                       <Scale size={20} />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-text-primary truncate">{activity.title}</p>
                      <p className="text-xs text-text-secondary truncate">{activity.subtitle}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-text-muted">{activity.date}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState 
                title={t('dashboard.empty_states.activity_title')}
                description={t('dashboard.empty_states.activity_desc')}
                icon={History}
                actionLabel={t('dashboard.empty_states.action_activity')}
                onAction={() => window.location.href = '/dashboard/settings?tab=integrations'}
                className="h-full border-0 bg-transparent py-12"
              />
            )}
          </div>
         </div>

          <div className="xl:col-span-1 bg-dark-bg border border-border rounded-xl p-5 relative overflow-hidden min-w-0">
            <WidgetRecentPRs prs={recentPRs} />
         </div>
      </div>

      {/* 5. NEW SECTION: PERFORMANCE & ANALYTICS */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          {/* Strength Radar */}
          <div className="bg-dark-bg border border-border rounded-xl p-5 relative overflow-hidden min-h-[300px]">
              <WidgetStrengthRadar data={strengthRadar} className="h-full w-full" />
          </div>

          {/* Volume Trend */}
          <div className="bg-dark-bg border border-border rounded-xl p-5 relative overflow-hidden min-h-[300px]">
              <WidgetVolumeTrend data={volumeTrend} className="h-full w-full flex flex-col justify-between" />
          </div>

           {/* Distribution & Summary */}
           <div className="space-y-6">
             <div className="bg-dark-bg border border-border rounded-xl p-5">
                <div className="flex justify-between items-center mb-4">
                   <div className="h-10 w-10 rounded bg-blue-500/10 text-blue-500 border border-blue-500/10 flex items-center justify-center">
                      <Dumbbell size={20} />
                   </div>
                   <div className="text-right">
                      <p className="text-xs text-text-secondary font-medium lowercase">{t('dashboard.goals_status', { completed: workouts.completed, target: workouts.target })}</p>
                   </div>
                </div>
                <WidgetWeeklyFrequency days={weeklyFrequency} />
             </div>

              <StatsCard
               title={t('dashboard.calories_today')}
               value={`${calories.consumed.toString()} kcal`}
               subtitle={t('dashboard.target_kcal', { target: calories.target })}
               icon={<Flame size={24} />}
               trend={calories.percent > 110 ? 'up' : calories.percent < 90 ? 'down' : 'stable'}
               trendValue={`${Math.round(calories.percent).toString()}%`}
               variant="orange"
             />
           </div>
      </div>
    </div>
  );
}
