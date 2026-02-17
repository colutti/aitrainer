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
import { useEffect } from 'react';
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { StatsCard } from '../../shared/components/ui/StatsCard';
import { useAuthStore } from '../../shared/hooks/useAuth';
import { useDashboardStore } from '../../shared/hooks/useDashboard';
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
  const { userInfo } = useAuthStore();

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  if (isLoading && !data) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-64 bg-dark-card rounded-3xl w-full" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-dark-card rounded-2xl" />
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
      weight_trend: 'stable' as const,
      body_fat_pct: null,
      muscle_mass_pct: null,
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

    const dateMap = new Map<string, Record<string, unknown>>();

    // Raw fat history
    if (data.fatHistory) {
      data.fatHistory.forEach(point => {
        const dateStr = typeof point.date === 'string' ? point.date : String(point.date);
        const dateKey = dateStr.split('T')[0] ?? dateStr;
        if (dateKey) {
          dateMap.set(dateKey, { date: dateKey, value: point.value });
        }
      });
    }

    // EMA trend data
    data.fatTrend.forEach(point => {
      const dateStr = typeof point.date === 'string' ? point.date : String(point.date);
      const dateKey = dateStr.split('T')[0] ?? dateStr;
      if (dateKey) {
        const existing = dateMap.get(dateKey) ?? { date: dateKey };
        existing.trend = point.value;  // EMA do backend
        dateMap.set(dateKey, existing);
      }
    });

    return Array.from(dateMap.values()).sort((a, b) => {
      const dateA = new Date(String(a.date)).getTime();
      const dateB = new Date(String(b.date)).getTime();
      return dateA - dateB;
    });
  };

  // Helper function for muscle trend data (merge raw + EMA)
  const getMergedMuscleData = () => {
    if (!data?.muscleTrend) return null;

    const dateMap = new Map<string, Record<string, unknown>>();

    // Raw muscle history
    if (data.muscleHistory) {
      data.muscleHistory.forEach(point => {
        const dateStr = typeof point.date === 'string' ? point.date : String(point.date);
        const dateKey = dateStr.split('T')[0] ?? dateStr;
        if (dateKey) {
          dateMap.set(dateKey, { date: dateKey, value: point.value });
        }
      });
    }

    // EMA trend data
    data.muscleTrend.forEach(point => {
      const dateStr = typeof point.date === 'string' ? point.date : String(point.date);
      const dateKey = dateStr.split('T')[0] ?? dateStr;
      if (dateKey) {
        const existing = dateMap.get(dateKey) ?? { date: dateKey };
        existing.trend = point.value;  // EMA do backend
        dateMap.set(dateKey, existing);
      }
    });

    return Array.from(dateMap.values()).sort((a, b) => {
      const dateA = new Date(String(a.date)).getTime();
      const dateB = new Date(String(b.date)).getTime();
      return dateA - dateB;
    });
  };

  const mergedWeightData = getMergedWeightData();
  const mergedFatData = getMergedFatData();
  const mergedMuscleData = getMergedMuscleData();

  const goalLabels: Record<string, string> = {
    'lose': 'Perda de Peso',
    'gain': 'Ganho de Massa',
    'maintain': 'Manutenção'
  };

  const confidenceColor = {
    'high': 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
    'medium': 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
    'low': 'text-orange-400 bg-orange-400/10 border-orange-400/20',
    'none': 'text-text-muted bg-white/5 border-white/10'
  }[metabolism.confidence] ?? 'text-text-muted';

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      
      {/* 1. Header & Quick Status */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-text-primary">
            Bom dia, <span className="text-gradient-start">{userInfo?.name ?? 'Atleta'}!</span>
          </h1>
          <p className="text-text-secondary mt-1">
            Aqui está o resumo do seu desempenho metabólico e físico.
          </p>
        </div>
        
        <div className="flex items-center gap-3 self-center md:self-end">
          {streak && (
            <WidgetStreak currentWeeks={streak.current_weeks} currentDays={streak.current_days} />
          )}
          <div className={cn("px-4 py-2 rounded-xl border text-[9px] font-bold uppercase tracking-widest h-[46px] flex items-center gap-2.5 shadow-sm backdrop-blur-sm transition-all", confidenceColor)}>
            <Activity size={18} className="opacity-80" />
            <div className="flex flex-col justify-center">
              <span className="text-text-muted/70 leading-none mb-1">Confiança</span>
              <span className="text-sm font-black leading-none">
               TDEE: {
                 metabolism.confidence === 'none' ? '---' :
                 ({
                   'high': 'Alta',
                   'medium': 'Média',
                   'low': 'Baixa'
                 }[metabolism.confidence.toLowerCase()] ?? 'Desconhecida')
               }
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. PRIORITY 1: METABOLISM & TDEE (The Engine) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Target Card */}
        <div className="lg:col-span-2 bg-gradient-to-br from-dark-card to-dark-card/50 border border-border rounded-3xl p-8 relative overflow-hidden group">
          <div className="relative z-10 flex flex-col md:flex-row justify-between gap-4 md:gap-8 h-full">
            <div className="space-y-6 flex-1">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-xl bg-gradient-start/10 text-gradient-start">
                  <Target size={24} />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-text-primary">Meta Diária</h2>
                  <p className="text-sm text-text-secondary">Foco: {goalLabels[metabolism.goal_type]}</p>
                </div>
              </div>
              
              <div>
                <span className="text-5xl md:text-6xl font-black text-white tracking-tight">
                  {metabolism.daily_target}
                </span>
                <span className="text-text-secondary ml-2 text-xl">kcal</span>
              </div>

              <div className="flex gap-6 pt-2">
                 <div>
                    <p className="text-xs text-text-muted uppercase font-bold tracking-wider mb-1">TDEE Real</p>
                    <p className="text-xl font-bold text-emerald-400 flex items-center gap-1">
                       <Zap size={16} /> {metabolism.tdee}
                    </p>
                 </div>
                 <div className="w-px bg-border h-10" />
                 <div>
                    <p className="text-xs text-text-muted uppercase font-bold tracking-wider mb-1">Tendência Semanal</p>
                    <p className={cn("text-xl font-bold flex items-center gap-1", metabolism.weekly_change > 0 ? "text-orange-400" : "text-blue-400")}>
                       <TrendingDown size={16} className={metabolism.weekly_change > 0 ? "rotate-180" : undefined} />
                       {Math.abs(metabolism.weekly_change).toFixed(2)} kg
                    </p>
                 </div>
              </div>
              
              <p className="text-[10px] text-text-muted italic mt-4 opacity-70 max-w-sm">
                * A tendência usa algoritmos para filtrar flutuações diárias de peso, garantindo maior precisão na sua meta.
              </p>
            </div>

            {/* Macro Preview (if available) */}
            {metabolism.macro_targets && (
              <div className="bg-white/5 rounded-2xl p-6 min-w-0 border border-white/5 backdrop-blur-sm">
                <h3 className="text-sm font-bold text-text-secondary mb-4 uppercase tracking-wider">Macros Sugeridos</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                     <span className="text-sm text-text-primary">Proteína</span>
                     <span className="font-bold text-emerald-400">{metabolism.macro_targets.protein}g</span>
                  </div>
                  <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                     <div className="h-full bg-emerald-500 w-full" />
                  </div>
                  
                  <div className="flex justify-between items-center">
                     <span className="text-sm text-text-primary">Gordura</span>
                     <span className="font-bold text-yellow-400">{metabolism.macro_targets.fat}g</span>
                  </div>
                   <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                     <div className="h-full bg-yellow-500 w-full" />
                  </div>

                  <div className="flex justify-between items-center">
                     <span className="text-sm text-text-primary">Carboidrato</span>
                     <span className="font-bold text-blue-400">{metabolism.macro_targets.carbs}g</span>
                  </div>
                   <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                     <div className="h-full bg-blue-500 w-full" />
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Decorative Blob */}
          <div className="absolute -right-20 -top-20 w-64 h-64 bg-gradient-start/10 rounded-full blur-3xl group-hover:bg-gradient-start/20 transition-all duration-1000" />
        </div>

        {/* Consistency Score */}
        <div className="bg-dark-card border border-border rounded-3xl p-6 flex flex-col justify-center items-center text-center space-y-4">
             <div className="relative w-32 h-32 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90">
                  <circle cx="64" cy="64" r="56" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-dark-bg" />
                  <circle cx="64" cy="64" r="56" stroke="currentColor" strokeWidth="8" fill="transparent" 
                          strokeDasharray={351} strokeDashoffset={351 - (351 * metabolism.consistency_score) / 100}
                          className="text-gradient-start transition-all duration-1000" />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center flex-col">
                   <span className="text-3xl font-bold">{metabolism.consistency_score}%</span>
                </div>
             </div>
             <div>
               <h3 className="font-bold text-lg text-text-primary">Consistência</h3>
               <p className="text-xs text-text-secondary mt-1">Qualidade dos seus registros recentes.</p>
             </div>
        </div>
      </div>

      {/* 3. PRIORITY 2: BODY COMPOSITION (The Result) */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Activity className="text-gradient-start" size={20} />
          <h2 className="text-xl font-bold text-text-primary">Composição Corporal</h2>
        </div>

        {/* Composition Charts - Grid: Weight + Fat on first row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Weight Card */}
          {data?.weightTrend && data.weightTrend.length > 0 && weightHistory && (
            <div className="bg-dark-card border border-border rounded-2xl p-6 relative overflow-hidden group">
              <div className="relative z-10 flex flex-col h-full">
                <div className="mb-4">
                  <p className="text-text-secondary text-sm font-medium mb-1">Peso Atual</p>
                  <h3 className="text-3xl font-bold text-text-primary tracking-tight flex items-center gap-2">
                    {body.weight_current.toFixed(2)} <span className="text-lg text-text-muted">kg</span>
                    <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
                      <Scale size={16} />
                    </div>
                  </h3>
                  <div className="flex flex-wrap items-center gap-2 mt-2 text-xs">
                    <span className={cn(
                      "font-bold px-2 py-0.5 rounded-full",
                      body.weight_diff > 0 ? 'bg-orange-500/10 text-orange-500' : 'bg-emerald-500/10 text-emerald-500'
                    )}>
                      {body.weight_diff > 0 ? '+' : ''}{body.weight_diff.toFixed(2)} kg <span className="text-text-muted ml-1">(7d)</span>
                    </span>
                    {body.weight_diff_15 !== undefined && body.weight_diff_15 !== null && (
                      <span className={cn(
                        "font-bold px-2 py-0.5 rounded-full",
                        body.weight_diff_15 > 0 ? 'bg-orange-500/10 text-orange-500' : 'bg-emerald-500/10 text-emerald-500'
                      )}>
                        {body.weight_diff_15 > 0 ? '+' : ''}{body.weight_diff_15.toFixed(2)} kg <span className="text-text-muted ml-1">(15d)</span>
                      </span>
                    )}
                    {body.weight_diff_30 !== undefined && body.weight_diff_30 !== null && (
                      <span className={cn(
                        "font-bold px-2 py-0.5 rounded-full",
                        body.weight_diff_30 > 0 ? 'bg-orange-500/10 text-orange-500' : 'bg-emerald-500/10 text-emerald-500'
                      )}>
                        {body.weight_diff_30 > 0 ? '+' : ''}{body.weight_diff_30.toFixed(2)} kg <span className="text-text-muted ml-1">(30d)</span>
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
                            backgroundColor: '#1e293b',
                            borderColor: '#334155',
                            borderRadius: '6px',
                            color: '#f8fafc',
                            fontSize: '11px',
                            padding: '6px'
                          }}
                          formatter={(value: number, name: string) => {
                            if (name === 'Tendência') return [value.toFixed(2), name];
                            return [value.toFixed(2), name];
                          }}
                          labelFormatter={(label) => {
                            const date = new Date(label as string);
                            return isNaN(date.getTime()) ? String(label) : date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
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
                          name="Peso"
                        />
                        {/* Tendência EMA (backend) - linha fina verde */}
                        <Line
                          type="monotone"
                          dataKey="trend"
                          stroke="#10b981"
                          strokeWidth={1}
                          dot={false}
                          isAnimationActive={false}
                          name="Tendência"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Legend */}
                <div className="flex gap-4 mt-3 text-xs">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-blue-400" />
                    <span className="text-text-muted">Peso (30d)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-emerald-500" />
                    <span className="text-text-muted">Tendência (30d)</span>
                  </div>
                </div>
              </div>
              {/* Background glow */}
              <div className="absolute right-0 top-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-3xl" />
            </div>
          )}

          {/* Fat Trend */}
          {data?.fatTrend && data.fatTrend.length > 0 && mergedFatData && (
            <div className="bg-dark-card border border-border rounded-2xl p-6 relative overflow-hidden group">
              <div className="relative z-10 flex flex-col h-full">
                <div className="mb-4">
                  <p className="text-text-secondary text-sm font-medium mb-1">Gordura Corporal</p>
                  <h3 className="text-3xl font-bold text-text-primary tracking-tight flex items-center gap-2">
                    {data.fatTrend[data.fatTrend.length - 1]?.value.toFixed(1) ?? '--'} <span className="text-lg text-text-muted">%</span>
                    <div className="w-8 h-8 rounded-lg bg-orange-500/10 text-orange-500 flex items-center justify-center">
                      <Flame size={16} />
                    </div>
                  </h3>
                  {body.fat_diff !== undefined && body.fat_diff !== null && (
                    <div className="flex flex-wrap items-center gap-2 mt-2 text-xs">
                      <span className={cn(
                        "font-bold px-2 py-0.5 rounded-full",
                        body.fat_diff > 0 ? 'bg-orange-500/10 text-orange-500' : 'bg-emerald-500/10 text-emerald-500'
                      )}>
                        {body.fat_diff > 0 ? '+' : ''}{body.fat_diff.toFixed(1)} % <span className="text-text-muted ml-1">(7d)</span>
                      </span>
                      {body.fat_diff_15 !== undefined && body.fat_diff_15 !== null && (
                        <span className={cn(
                          "font-bold px-2 py-0.5 rounded-full",
                          body.fat_diff_15 > 0 ? 'bg-orange-500/10 text-orange-500' : 'bg-emerald-500/10 text-emerald-500'
                        )}>
                          {body.fat_diff_15 > 0 ? '+' : ''}{body.fat_diff_15.toFixed(1)} % <span className="text-text-muted ml-1">(15d)</span>
                        </span>
                      )}
                      {body.fat_diff_30 !== undefined && body.fat_diff_30 !== null && (
                        <span className={cn(
                          "font-bold px-2 py-0.5 rounded-full",
                          body.fat_diff_30 > 0 ? 'bg-orange-500/10 text-orange-500' : 'bg-emerald-500/10 text-emerald-500'
                        )}>
                          {body.fat_diff_30 > 0 ? '+' : ''}{body.fat_diff_30.toFixed(1)} % <span className="text-text-muted ml-1">(30d)</span>
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Fat chart with two lines */}
                <div className="flex-1 min-h-[120px] -mx-2 -mb-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={mergedFatData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                      <XAxis dataKey="date" hide />
                      <YAxis hide domain={['dataMin - 0.5', 'dataMax + 0.5']} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1e293b',
                          borderColor: '#334155',
                          borderRadius: '6px',
                          color: '#f8fafc',
                          fontSize: '11px',
                          padding: '6px'
                        }}
                        formatter={(value: number, name: string) => {
                          if (name === 'Tendência') return [value.toFixed(2), name];
                          return [value.toFixed(1), name];
                        }}
                        labelFormatter={(label) => {
                          const date = new Date(label as string);
                          return isNaN(date.getTime()) ? String(label) : date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
                        }}
                      />
                      {/* Gordura Real - linha mais grossa laranja (destaque) */}
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#f97316"
                        strokeWidth={2.5}
                        dot={false}
                        isAnimationActive={false}
                        name="Gordura"
                      />
                      {/* Tendência EMA (backend) - linha fina verde */}
                      <Line
                        type="monotone"
                        dataKey="trend"
                        stroke="#10b981"
                        strokeWidth={1}
                        dot={false}
                        isAnimationActive={false}
                        name="Tendência"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* Legend */}
                <div className="flex gap-4 mt-3 text-xs">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-orange-500" />
                    <span className="text-text-muted">Gordura (30d)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-emerald-500" />
                    <span className="text-text-muted">Tendência (30d)</span>
                  </div>
                </div>
              </div>
              {/* Background glow */}
              <div className="absolute right-0 top-0 w-32 h-32 bg-orange-500/5 rounded-full blur-3xl" />
            </div>
          )}
        </div>

        {/* Composition Charts - Row 2: Muscle + BMR */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Muscle Trend */}
          {data?.muscleTrend && data.muscleTrend.length > 0 && mergedMuscleData && (
            <div className="bg-dark-card border border-border rounded-2xl p-6 relative overflow-hidden group">
              <div className="relative z-10 flex flex-col h-full">
                <div className="mb-4">
                  <p className="text-text-secondary text-sm font-medium mb-1">Massa Muscular</p>
                  <h3 className="text-3xl font-bold text-text-primary tracking-tight flex items-center gap-2">
                    {data.muscleTrend[data.muscleTrend.length - 1]?.value.toFixed(1) ?? '--'} <span className="text-lg text-text-muted">%</span>
                    <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-500 flex items-center justify-center">
                      <Dumbbell size={16} />
                    </div>
                  </h3>
                  {body.muscle_diff !== undefined && body.muscle_diff !== null && (
                    <div className="flex flex-wrap items-center gap-2 mt-2 text-xs">
                      <span className={cn(
                        "font-bold px-2 py-0.5 rounded-full",
                        body.muscle_diff > 0 ? 'bg-emerald-500/10 text-emerald-500' : 'bg-orange-500/10 text-orange-500'
                      )}>
                        {body.muscle_diff > 0 ? '+' : ''}{body.muscle_diff.toFixed(1)} % <span className="text-text-muted ml-1">(7d)</span>
                      </span>
                      {body.muscle_diff_15 !== undefined && body.muscle_diff_15 !== null && (
                        <span className={cn(
                          "font-bold px-2 py-0.5 rounded-full",
                          body.muscle_diff_15 > 0 ? 'bg-emerald-500/10 text-emerald-500' : 'bg-orange-500/10 text-orange-500'
                        )}>
                          {body.muscle_diff_15 > 0 ? '+' : ''}{body.muscle_diff_15.toFixed(1)} % <span className="text-text-muted ml-1">(15d)</span>
                        </span>
                      )}
                      {body.muscle_diff_30 !== undefined && body.muscle_diff_30 !== null && (
                        <span className={cn(
                          "font-bold px-2 py-0.5 rounded-full",
                          body.muscle_diff_30 > 0 ? 'bg-emerald-500/10 text-emerald-500' : 'bg-orange-500/10 text-orange-500'
                        )}>
                          {body.muscle_diff_30 > 0 ? '+' : ''}{body.muscle_diff_30.toFixed(1)} % <span className="text-text-muted ml-1">(30d)</span>
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Muscle chart with two lines */}
                <div className="flex-1 min-h-[120px] -mx-2 -mb-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={mergedMuscleData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                      <XAxis dataKey="date" hide />
                      <YAxis hide domain={['dataMin - 0.5', 'dataMax + 0.5']} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1e293b',
                          borderColor: '#334155',
                          borderRadius: '6px',
                          color: '#f8fafc',
                          fontSize: '11px',
                          padding: '6px'
                        }}
                        formatter={(value: number, name: string) => {
                          if (name === 'Tendência') return [value.toFixed(2), name];
                          return [value.toFixed(1), name];
                        }}
                        labelFormatter={(label) => {
                          const date = new Date(label as string);
                          return isNaN(date.getTime()) ? String(label) : date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
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
                        name="Músculo"
                      />
                      {/* Tendência EMA (backend) - linha fina verde */}
                      <Line
                        type="monotone"
                        dataKey="trend"
                        stroke="#10b981"
                        strokeWidth={1}
                        dot={false}
                        isAnimationActive={false}
                        name="Tendência"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* Legend */}
                <div className="flex gap-4 mt-3 text-xs">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-blue-500" />
                    <span className="text-text-muted">Músculo (30d)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-emerald-500" />
                    <span className="text-text-muted">Tendência (30d)</span>
                  </div>
                </div>
              </div>
              {/* Background glow */}
              <div className="absolute right-0 top-0 w-32 h-32 bg-blue-500/5 rounded-full blur-3xl" />
            </div>
          )}
        </div>
      </div>

      {/* 4. PRIORITY 3: DAILY TRACKING (The Action) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
         <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center gap-2">
              <History className="text-gradient-start" size={20} />
              <h2 className="text-xl font-bold text-text-primary">Atividade Recente</h2>
            </div>
            <div className="bg-dark-card border border-border rounded-2xl overflow-hidden">
            {data?.recentActivities.length ? (
              <div className="divide-y divide-border">
                {data.recentActivities.map((activity) => (
                  <div key={activity.id} className="p-4 flex items-center gap-4 hover:bg-white/5 transition-colors group">
                    <div className="w-10 h-10 rounded-lg bg-dark-bg border border-border flex items-center justify-center text-text-secondary group-hover:text-gradient-start transition-colors">
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
              <div className="p-12 text-center">
                <p className="text-text-muted">Nenhuma atividade registrada.</p>
              </div>
            )}
          </div>
         </div>

         <div className="lg:col-span-1">
            {recentPRs && <WidgetRecentPRs prs={recentPRs} />}
         </div>
      </div>

      {/* 5. NEW SECTION: PERFORMANCE & ANALYTICS */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Strength Radar */}
          <div className="bg-dark-card border border-border rounded-2xl p-6 relative overflow-hidden min-h-[300px]">
             {strengthRadar ? (
               <WidgetStrengthRadar data={strengthRadar} className="h-full w-full" />
             ) : (
                <div className="h-full flex items-center justify-center text-text-muted">
                   <p>Dados de força insuficientes</p>
                </div>
             )}
          </div>

          {/* Volume Trend */}
          <div className="bg-dark-card border border-border rounded-2xl p-6 relative overflow-hidden min-h-[300px]">
             {volumeTrend ? (
               <WidgetVolumeTrend data={volumeTrend} className="h-full w-full flex flex-col justify-between" />
             ) : (
                <div className="h-full flex items-center justify-center text-text-muted">
                   <p>Histórico de volume indisponível</p>
                </div>
             )}
          </div>

           {/* Distribution & Summary */}
           <div className="space-y-6">
             <div className="bg-dark-card border border-border rounded-2xl p-6">
                <div className="flex justify-between items-center mb-4">
                   <div className="h-10 w-10 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center">
                      <Dumbbell size={20} />
                   </div>
                   <div className="text-right">
                      <p className="text-xs text-text-secondary font-medium lowercase">Metas: {workouts.completed}/{workouts.target}</p>
                   </div>
                </div>
                {weeklyFrequency && <WidgetWeeklyFrequency days={weeklyFrequency} />}
             </div>

              <StatsCard
               title="Calorias Hoje"
               value={`${calories.consumed.toString()} kcal`}
               subtitle={`Meta: ${calories.target.toString()} kcal`}
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
