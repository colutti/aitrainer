import { 
  Activity,
  ChevronRight,
  Droplets,
  History,
  Plus, 
  Scale, 
  TrendingUp, 
  Upload, 
  Zap
} from 'lucide-react';
import { useEffect } from 'react';

import { Button } from '../../shared/components/ui/Button';
import { StatsCard } from '../../shared/components/ui/StatsCard';
import { useBodyStore } from '../../shared/hooks/useBody';
import { useConfirmation } from '../../shared/hooks/useConfirmation';
import { useNotificationStore } from '../../shared/hooks/useNotification';

import { WeightLogCard } from './components/WeightLogCard';

/**
 * BodyPage component
 * 
 * Tracks weight, body composition, and physical metrics.
 */
export function BodyPage() {
  const { 
    logs, 
    stats, 
    isLoading, 
    fetchLogs, 
    fetchStats, 
    deleteLog 
  } = useBodyStore();
  
  const { confirm } = useConfirmation();
  const notify = useNotificationStore();

  useEffect(() => {
    void fetchLogs();
    void fetchStats();
  }, [fetchLogs, fetchStats]);

  const handleDelete = async (date: string) => {
    const isConfirmed = await confirm({
      title: 'Excluir Registro',
      message: 'Tem certeza que deseja excluir este registro de peso? Isso pode afetar seus cálculos de TDEE.',
      confirmText: 'Excluir',
      type: 'danger',
    });

    if (isConfirmed) {
      try {
        await deleteLog(date);
        notify.success('Registro excluído com sucesso!');
      } catch {
        notify.error('Erro ao excluir registro.');
      }
    }
  };

  const latest = stats?.latest;

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
            <Scale className="text-gradient-start" size={32} />
            Corpo & Peso
          </h1>
          <p className="text-text-secondary mt-1">
            Monitore sua composição corporal e tendências.
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" size="lg" className="gap-2">
            <Upload size={20} />
            Importar Balança
          </Button>
          <Button variant="primary" size="lg" className="shadow-orange gap-2">
            <Plus size={20} />
            Registrar Peso
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Peso Atual"
          value={`${latest?.weight_kg.toFixed(1) ?? '--'} kg`}
          subtitle={latest?.date ? `Último registro em ${new Date(latest.date).toLocaleDateString('pt-BR')}` : 'Sem registros'}
          icon={<Scale size={24} />}
          trend={latest?.trend_weight ? {
            value: `${Math.abs(latest.weight_kg - latest.trend_weight).toFixed(1)} kg`,
            isPositive: latest.weight_kg < latest.trend_weight,
            label: 'vs. tendência'
          } : undefined}
          variant="primary"
        />
        <StatsCard
          title="Gordura Corporal"
          value={`${latest?.body_fat_pct?.toFixed(1) ?? '--'}%`}
          subtitle="Composição Corporal"
          icon={<Activity size={24} />}
          variant="secondary"
        />
        <StatsCard
          title="Massa Muscular"
          value={`${latest?.muscle_mass_pct?.toFixed(1) ?? '--'}%`}
          subtitle="Estimativa de Massa Magra"
          icon={<Zap size={24} />}
          variant="secondary"
        />
        <StatsCard
          title="BMR Estimado"
          value={latest?.bmr?.toString() ?? '--'}
          subtitle="Calorias Basais (kcal)"
          icon={<Droplets size={24} />}
          variant="secondary"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* History */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History className="text-gradient-start" size={20} />
              <h2 className="text-xl font-bold text-text-primary">Histórico de Peso</h2>
            </div>
            <Button variant="ghost" size="sm" className="gap-1">
              Ver Gráficos <ChevronRight size={16} />
            </Button>
          </div>

          <div className="space-y-3">
            {isLoading && logs.length === 0 ? (
              [1, 2, 3].map((i) => (
                <div key={i} className="h-20 bg-dark-card rounded-2xl animate-pulse" />
              ))
            ) : logs.length > 0 ? (
              logs.map((log) => (
                <WeightLogCard 
                  key={log.date} 
                  log={log} 
                  onDelete={(date) => {
                    void handleDelete(date);
                  }}
                />
              ))
            ) : (
              <div className="p-12 text-center bg-dark-card rounded-2xl border border-border border-dashed">
                <p className="text-text-muted">Nenhum registro de peso encontrado.</p>
              </div>
            )}
          </div>
        </div>

        {/* Insights */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="text-gradient-start" size={20} />
            <h2 className="text-xl font-bold text-text-primary">Visão Geral</h2>
          </div>
          
          <div className="bg-dark-card border border-border rounded-2xl p-6 space-y-6">
            <div className="space-y-2">
              <h3 className="font-bold text-text-primary">Tendência de Peso</h3>
              <p className="text-sm text-text-secondary">
                Sua tendência atual é de <span className="text-emerald-400 font-bold">manutenção</span>. 
                A média móvel ajuda a ignorar flutuações diárias causadas por sódio e água.
              </p>
            </div>
            
            <div className="space-y-4">
              <div className="bg-dark-bg/50 rounded-xl p-4 border border-border/50">
                <p className="text-xs text-text-muted font-bold uppercase">BMI (IMC)</p>
                <div className="flex items-end justify-between mt-1">
                  <p className="text-2xl font-bold text-text-primary">{latest?.bmi?.toFixed(1) ?? '--'}</p>
                  <span className="text-[10px] bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded-full font-bold uppercase mb-1">
                    Normal
                  </span>
                </div>
              </div>
              
              <div className="bg-dark-bg/50 rounded-xl p-4 border border-border/50">
                <p className="text-xs text-text-muted font-bold uppercase">Peso da Tendência</p>
                <p className="text-2xl font-bold text-text-primary mt-1">
                  {latest?.trend_weight?.toFixed(1) ?? '--'} <span className="text-sm font-normal text-text-secondary">kg</span>
                </p>
              </div>
            </div>

            <p className="text-[10px] text-text-muted italic leading-relaxed">
              * Dados baseados no seu histórico recente. 
              Pesagem diária em jejum é recomendada para maior precisão da tendência.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
