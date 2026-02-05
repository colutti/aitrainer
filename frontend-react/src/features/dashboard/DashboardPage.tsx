import { 
  Scale, 
  Flame, 
  Dumbbell, 
  Droplets,
  TrendingUp,
  History,
  Calendar,
  ChevronRight
} from 'lucide-react';
import { useEffect } from 'react';

import { Button } from '../../shared/components/ui/Button';
import { StatsCard } from '../../shared/components/ui/StatsCard';
import { useDashboardStore } from '../../shared/hooks/useDashboard';

/**
 * DashboardPage component
 * 
 * Main landing page for authenticated users.
 * Displays user statistics, recent activities, and AI personal insights.
 */
export function DashboardPage() {
  const { data, isLoading, fetchData } = useDashboardStore();

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  if (isLoading && !data) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-20 bg-dark-card rounded-2xl w-full" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-dark-card rounded-2xl" />
          ))}
        </div>
      </div>
    );
  }

  const stats = data?.stats ?? {
    weight: { current: 0, difference: 0, trend: 'stable' as const },
    calories: { consumed: 0, target: 0, percent: 0 },
    workouts: { completed: 0, target: 0 },
    water: { consumed: 0, target: 0 },
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Welcome Header */}
      <div className="relative overflow-hidden bg-gradient-to-r from-gradient-start/10 to-gradient-end/10 rounded-3xl p-8 border border-gradient-start/20">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h1 className="text-3xl font-bold text-text-primary mb-2">
              Bom dia, <span className="text-gradient-start">Atleta!</span>
            </h1>
            <p className="text-text-secondary max-w-lg">
              Você está no caminho certo. Hoje é um ótimo dia para bater suas metas. 
              Seu treinador de IA recomenda focar no treino de pernas hoje.
            </p>
          </div>
          <Button variant="primary" size="lg" className="shadow-orange shrink-0">
            Começar Treino
          </Button>
        </div>
        
        {/* Decorative background element */}
        <div className="absolute -right-20 -bottom-20 w-64 h-64 bg-gradient-start/10 rounded-full blur-3xl" />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Peso Atual"
          value={`${stats.weight.current.toString()} kg`}
          subtitle={`Meta: ${(stats.weight.current - 5).toString()} kg`}
          icon={<Scale size={24} />}
          trend={stats.weight.trend}
          trendValue={`${stats.weight.difference > 0 ? '+' : ''}${stats.weight.difference.toString()} kg este mês`}
          variant="primary"
        />
        <StatsCard
          title="Calorias"
          value={`${stats.calories.consumed.toString()} kcal`}
          subtitle={`Meta: ${stats.calories.target.toString()} kcal`}
          icon={<Flame size={24} />}
          trend={stats.calories.percent > 90 ? 'up' : 'down'}
          trendValue={`${stats.calories.percent.toString()}% da meta diária`}
          variant="orange"
        />
        <StatsCard
          title="Treinos na Semana"
          value={`${stats.workouts.completed.toString()}/${stats.workouts.target.toString()}`}
          subtitle={stats.workouts.lastWorkoutDate ? `Último: ${stats.workouts.lastWorkoutDate}` : 'Nenhum treino ainda'}
          icon={<Dumbbell size={24} />}
          variant="blue"
        />
        <StatsCard
          title="Hidratação"
          value={`${stats.water.consumed.toString()} ml`}
          subtitle={`Meta: ${stats.water.target.toString()} ml`}
          icon={<Droplets size={24} />}
          variant="green"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Activity */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History className="text-gradient-start" size={20} />
              <h2 className="text-xl font-bold text-text-primary">Atividade Recente</h2>
            </div>
            <Button variant="ghost" size="sm" className="gap-1">
              Ver tudo <ChevronRight size={16} />
            </Button>
          </div>

          <div className="bg-dark-card border border-border rounded-2xl overflow-hidden">
            {data?.recentActivities.length ? (
              <div className="divide-y divide-border">
                {data.recentActivities.map((activity) => (
                  <div key={activity.id} className="p-4 flex items-center gap-4 hover:bg-white/5 transition-colors group">
                    <div className="w-10 h-10 rounded-lg bg-dark-bg border border-border flex items-center justify-center text-text-secondary group-hover:text-gradient-start transition-colors">
                      <Calendar size={20} />
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
                <p className="text-text-muted">Nenhuma atividade registrada nos últimos 7 dias.</p>
              </div>
            )}
          </div>
        </div>

        {/* AI Insight / Progress */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="text-gradient-start" size={20} />
            <h2 className="text-xl font-bold text-text-primary">Evolução</h2>
          </div>
          
          <div className="bg-dark-card border border-border rounded-2xl p-6 h-full">
            <div className="flex flex-col items-center justify-center text-center h-full space-y-4">
              <div className="w-24 h-24 rounded-full border-4 border-gradient-start/20 border-t-gradient-start flex items-center justify-center mb-2">
                <span className="text-2xl font-bold">75%</span>
              </div>
              <div>
                <h3 className="font-bold text-lg">Quase lá!</h3>
                <p className="text-sm text-text-secondary mt-1">
                  Você completou 75% da sua meta de treinos nesta semana. 
                  Apenas mais um para atingir seu objetivo.
                </p>
              </div>
              <Button variant="secondary" fullWidth>
                Ver Detalhes
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
