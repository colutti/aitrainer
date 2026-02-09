import { 
  Zap, 
  Target, 
  AlertCircle,
  BarChart3,
  TrendingDown,
  Info
} from 'lucide-react';

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
    'high': 'Alta Confiança',
    'medium': 'Confiança Média',
    'low': 'Poucos Dados',
    'none': 'Dados Insuficientes'
  }[stats?.confidence ?? 'none'];

  const goalLabels: Record<string, string> = {
    'lose': 'Perda de Peso',
    'gain': 'Ganho de Massa',
    'maintain': 'Manutenção'
  };

  return (
    <div className="space-y-10">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatsCard
          title="TDEE Atual"
          value={`${stats?.tdee.toString() ?? '--'} kcal`}
          subtitle="Gasto Energético Total"
          icon={<Zap size={24} />}
          variant="primary"
        />
        <StatsCard
          title="Meta Recomendada"
          value={`${stats?.daily_target.toString() ?? '--'} kcal`}
          subtitle={`Foco: ${goalLabels[stats?.goal_type ?? ''] ?? 'Manutenção'}`}
          icon={<Target size={24} />}
          variant="orange"
        />
        <StatsCard
          title="Taxa de Variação"
          value={`${stats?.weight_change_per_week ? (stats.weight_change_per_week > 0 ? '+' : '') + stats.weight_change_per_week.toFixed(2) : '--'} kg`}
          subtitle="Média por semana"
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
               <h2 className="text-xl font-bold text-text-primary">Análise Metabólica</h2>
             </div>
             <div className={cn("text-[10px] font-bold uppercase tracking-widest px-2 py-1 bg-white/5 rounded-lg border border-border/50", confidenceColor)}>
               {confidenceText}
             </div>
          </div>

          <div className="space-y-6">
            <div className="flex gap-4">
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
                   {period} sem
                 </button>
               ))}
            </div>

            <div className="p-4 bg-dark-bg border border-border rounded-xl space-y-4">
               <div className="flex justify-between items-center text-sm">
                 <span className="text-text-secondary">Déficit/Superávit Médio</span>
                 <span className={cn("font-bold", (stats?.energy_balance ?? 0) < 0 ? "text-red-400" : "text-emerald-400")}>
                    {(stats?.energy_balance ?? 0) > 0 ? '+' : ''}{stats?.energy_balance ?? 0} kcal
                 </span>
               </div>
               <div className="flex justify-between items-center text-sm">
                 <span className="text-text-secondary">Duração da Análise</span>
                 <span className="text-text-primary font-bold">{weeks} semanas</span>
               </div>
            </div>

            <div className="p-4 bg-blue-500/5 border border-blue-500/10 rounded-xl flex gap-3">
               <Info className="text-blue-400 shrink-0" size={18} />
               <p className="text-xs text-text-secondary leading-relaxed">
                 O TDEE é calculado comparando sua ingestão calórica com a variação na tendência do seu peso corporal. 
                 Quanto mais dias você registrar peso e calorias, mais precisa será a estimativa.
               </p>
            </div>
          </div>
        </section>

        {/* Metabolic Outlook */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-dark-card border border-border rounded-3xl p-8 relative overflow-hidden group">
             <div className="relative z-10 space-y-4">
                <TrendingDown className="text-emerald-400" size={40} />
                <h2 className="text-2xl font-bold text-text-primary">Plano Sugerido</h2>
                <p className="text-text-secondary text-lg leading-relaxed max-w-xl">
                  {stats?.confidence === 'none' 
                    ? 'Precisamos de pelo menos 7 dias de registros consistentes para gerar um plano sugerido.' 
                    : `Para atingir seu objetivo de ${goalLabels[stats?.goal_type ?? '']?.toLowerCase() ?? 'manutenção'}, sugerimos manter uma ingestão de ${String(stats?.daily_target)} kcal diárias.`
                  }
                </p>
                <div className="pt-4 flex gap-4">
                   <div className="text-center">
                     <p className="text-[10px] text-text-muted uppercase font-bold tracking-widest mb-1">Proteína</p>
                     <p className="text-xl font-bold text-text-primary">~{stats?.macro_targets?.protein ?? '--'}g</p>
                   </div>
                   <div className="w-px h-10 bg-border mx-2" />
                   <div className="text-center">
                     <p className="text-[10px] text-text-muted uppercase font-bold tracking-widest mb-1">Gordura</p>
                     <p className="text-xl font-bold text-text-primary">~{stats?.macro_targets?.fat ?? '--'}g</p>
                   </div>
                   <div className="w-px h-10 bg-border mx-2" />
                   <div className="text-center">
                     <p className="text-[10px] text-text-muted uppercase font-bold tracking-widest mb-1">Carboidratos</p>
                     <p className="text-xl font-bold text-text-primary">~{stats?.macro_targets?.carbs ?? '--'}g</p>
                   </div>
                </div>
             </div>
             <div className="absolute -right-20 -bottom-20 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl group-hover:bg-emerald-500/10 transition-colors duration-700" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
             <div className="bg-dark-card border border-border rounded-2xl p-6">
                <h4 className="text-sm font-bold text-text-primary mb-4">Qualidade dos Dados</h4>
                <div className="space-y-4">
                   <div className="space-y-1">
                      <div className="flex justify-between text-xs mb-1">
                         <span className="text-text-secondary">Consistência Geral</span>
                         <span className="text-text-primary font-bold">{stats?.consistency_score ?? 0}%</span>
                      </div>
                      <div className="w-full h-1.5 bg-dark-bg rounded-full overflow-hidden">
                         <div className="h-full bg-blue-500 transition-all duration-1000" style={{ width: `${String(stats?.consistency_score ?? 0)}%` }} />
                      </div>
                   </div>
                   <div className="space-y-1">
                      <div className="flex justify-between text-xs mb-1">
                         <span className="text-text-secondary">Estabilidade Calórica</span>
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
                   <p className="text-xs text-text-muted font-bold uppercase tracking-widest">Consumo Sugerido</p>
                   <p className="text-4xl font-bold text-gradient-start">{stats?.daily_target ?? '--'}</p>
                   <p className="text-[10px] text-text-secondary">kcal / dia</p>
                </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
