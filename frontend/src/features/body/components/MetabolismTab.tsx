import { 
  Zap, 
  Target, 
  AlertCircle,
  BarChart3,
  TrendingDown,
  Info
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { StatsCard } from '../../../shared/components/ui/StatsCard';
import { cn } from '../../../shared/utils/cn';
import { useMetabolismTab } from '../hooks/useMetabolismTab';

export function MetabolismTab() {
  const {
    stats,
    isLoading,
    weeks,
    setWeeks
  } = useMetabolismTab();
  const { t } = useTranslation();

  if (isLoading && !stats) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 bg-dark-card rounded-2xl" />
          ))}
        </div>
        <div className="h-96 bg-dark-card rounded-2xl" />
      </div>
    );
  }

  const confidenceColor = {
    'high': 'text-emerald-400',
    'medium': 'text-yellow-400',
    'low': 'text-orange-400',
    'none': 'text-text-muted'
  }[stats?.confidence ?? 'none'];

  const confidenceText = {
    'high': t('body.metabolism.confidence.high'),
    'medium': t('body.metabolism.confidence.medium'),
    'low': t('body.metabolism.confidence.low'),
    'none': t('body.metabolism.confidence.none')
  }[stats?.confidence ?? 'none'];

  const goalLabels: Record<string, string> = {
    'lose': t('body.metabolism.goals.lose'),
    'gain': t('body.metabolism.goals.gain'),
    'maintain': t('body.metabolism.goals.maintain')
  };

  return (
    <div className="space-y-10">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatsCard
          title={t('body.metabolism.current_tdee')}
          value={`${stats?.tdee.toString() ?? '--'} kcal`}
          subtitle={t('body.metabolism.tdee_subtitle')}
          icon={<Zap size={24} />}
          variant="primary"
        />
        <StatsCard
          title={t('body.metabolism.recommended_goal')}
          value={`${stats?.daily_target.toString() ?? '--'} kcal`}
          subtitle={t('body.metabolism.focus', { goal: goalLabels[stats?.goal_type ?? 'maintain'] ?? goalLabels.maintain ?? '' })}
          icon={<Target size={24} />}
          variant="orange"
        />
        <StatsCard
          title={t('body.metabolism.change_rate')}
          value={`${stats?.weight_change_per_week ? (stats.weight_change_per_week > 0 ? '+' : '') + stats.weight_change_per_week.toFixed(2) : '--'} kg`}
          subtitle={t('body.metabolism.avg_per_week')}
          icon={<BarChart3 size={24} />}
          variant="secondary"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Analysis Card */}
        <section className="bg-dark-card border border-border rounded-2xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-border pb-4">
             <div className="flex items-center gap-2">
               <AlertCircle className="text-gradient-start" size={20} />
               <h2 className="text-xl font-bold text-text-primary">{t('body.metabolism.analysis_title')}</h2>
             </div>
             <div className={cn("text-[10px] font-bold uppercase tracking-widest px-2 py-1 bg-white/5 rounded-lg border border-border/50", confidenceColor)}>
               {confidenceText}
             </div>
          </div>

          <div className="space-y-6">
            <div className="flex gap-2 md:gap-4">
               {[2, 4, 8, 12].map(period => (
                 <button
                   key={period}
                   onClick={() => { setWeeks(period); }}
                   className={cn(
                     "flex-1 py-2 text-xs font-bold rounded-xl border transition-all",
                     weeks === period
                       ? "bg-gradient-start border-gradient-start text-white shadow-orange-sm"
                       : "bg-dark-bg border-border text-text-secondary hover:border-gradient-start/30"
                   )}
                 >
                   {t('body.metabolism.weeks', { count: period })}
                 </button>
               ))}
            </div>

            <div className="p-4 bg-dark-bg border border-border rounded-xl space-y-4">
               <div className="flex justify-between items-center text-sm">
                 <span className="text-text-secondary">{t('body.metabolism.avg_balance')}</span>
                 <span className={cn("font-bold", (stats?.energy_balance ?? 0) < 0 ? "text-red-400" : "text-emerald-400")}>
                    {(stats?.energy_balance ?? 0) > 0 ? '+' : ''}{stats?.energy_balance ?? 0} kcal
                 </span>
               </div>
               <div className="flex justify-between items-center text-sm">
                 <span className="text-text-secondary">{t('body.metabolism.analysis_duration')}</span>
                 <span className="text-text-primary font-bold">{t('body.metabolism.weeks_plural', { count: weeks })}</span>
               </div>
            </div>

            <div className="p-4 bg-blue-500/5 border border-blue-500/10 rounded-xl flex gap-3">
               <Info className="text-blue-400 shrink-0" size={18} />
               <p className="text-xs text-text-secondary leading-relaxed">
                 {t('body.metabolism.info_desc')}
               </p>
            </div>
          </div>
        </section>

        {/* Metabolic Outlook */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-dark-card border border-border rounded-3xl p-8 relative overflow-hidden group">
             <div className="relative z-10 space-y-4">
                <TrendingDown className="text-emerald-400" size={40} />
                <h2 className="text-2xl font-bold text-text-primary">{t('body.metabolism.plan_title')}</h2>
                <p className="text-text-secondary text-lg leading-relaxed max-w-xl">
                  {stats?.confidence === 'none'
                    ? t('body.metabolism.insufficient_data')
                    : t('body.metabolism.plan_desc', {
                        goal: (goalLabels[stats?.goal_type ?? 'maintain'] ?? goalLabels.maintain ?? '').toLowerCase(),
                        target: stats?.daily_target
                      })
                  }
                </p>
                <div className="pt-4 flex flex-col md:flex-row gap-4 md:gap-0">
                   <div className="text-center flex-1">
                     <p className="text-[10px] text-text-muted uppercase font-bold tracking-widest mb-1">{t('nutrition.protein_short')}</p>
                     <p className="text-xl font-bold text-text-primary">~{stats?.macro_targets?.protein ?? '--'}g</p>
                   </div>
                   <div className="hidden md:block w-px h-10 bg-border" />
                   <div className="text-center flex-1">
                     <p className="text-[10px] text-text-muted uppercase font-bold tracking-widest mb-1">{t('nutrition.fat_short')}</p>
                     <p className="text-xl font-bold text-text-primary">~{stats?.macro_targets?.fat ?? '--'}g</p>
                   </div>
                   <div className="hidden md:block w-px h-10 bg-border" />
                   <div className="text-center flex-1">
                     <p className="text-[10px] text-text-muted uppercase font-bold tracking-widest mb-1">{t('nutrition.carbs_short')}</p>
                     <p className="text-xl font-bold text-text-primary">~{stats?.macro_targets?.carbs ?? '--'}g</p>
                   </div>
                </div>
             </div>
             <div className="absolute -right-20 -bottom-20 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl group-hover:bg-emerald-500/10 transition-colors duration-700" />
          </div>
 
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
             <div className="bg-dark-card border border-border rounded-2xl p-6">
                <h4 className="text-sm font-bold text-text-primary mb-4">{t('body.metabolism.data_quality')}</h4>
                <div className="space-y-4">
                   <div className="space-y-1">
                      <div className="flex justify-between text-xs mb-1">
                         <span className="text-text-secondary">{t('body.metabolism.general_consistency')}</span>
                         <span className="text-text-primary font-bold">{stats?.consistency_score ?? 0}%</span>
                      </div>
                      <div className="w-full h-1.5 bg-dark-bg rounded-full overflow-hidden">
                         <div className="h-full bg-blue-500 transition-all duration-1000" style={{ width: `${String(stats?.consistency_score ?? 0)}%` }} />
                      </div>
                   </div>
                   <div className="space-y-1">
                      <div className="flex justify-between text-xs mb-1">
                         <span className="text-text-secondary">{t('body.metabolism.caloric_stability')}</span>
                         <span className="text-text-primary font-bold">{stats?.stability_score ?? 0}%</span>
                      </div>
                      <div className="w-full h-1.5 bg-dark-bg rounded-full overflow-hidden">
                         <div className="h-full bg-orange-500 transition-all duration-1000" style={{ width: `${String(stats?.stability_score ?? 0)}%` }} />
                      </div>
                   </div>
                </div>
             </div>
             
             <div className="bg-gradient-start/5 border border-gradient-start/20 rounded-2xl p-6 flex items-center justify-center text-center">
                <div className="space-y-2">
                   <p className="text-xs text-text-muted font-bold uppercase tracking-widest">{t('body.metabolism.suggested_consumption')}</p>
                   <p className="text-4xl font-bold text-gradient-start">{stats?.daily_target ?? '--'}</p>
                   <p className="text-[10px] text-text-secondary">kcal / {t('common.day')}</p>
                </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
