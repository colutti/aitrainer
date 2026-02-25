import { Users, Activity, MessageSquare, Dumbbell, AlertTriangle, TrendingUp } from 'lucide-react';
import { useEffect, useState } from 'react';

import { StatsCard } from '../../../../../src/shared/components/ui/StatsCard';
import type { AdminOverview, QualityMetrics } from '../../../../../src/shared/types/admin';
import { adminApi } from '../api/admin-api';

export function AdminDashboardPage() {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [metrics, setMetrics] = useState<QualityMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setIsLoading(true);
        const [overviewData, metricsData] = await Promise.all([
          adminApi.getOverview(),
          adminApi.getQualityMetrics()
        ]);
        setOverview(overviewData);
        setMetrics(metricsData);
      } catch {
        // console.error(err);
        setError('Erro ao carregar dados do dashboard.');
      } finally {
        setIsLoading(false);
      }
    }
    void loadData();
  }, []);

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/20 text-red-500 p-4 rounded-xl flex items-center gap-2">
        <AlertTriangle size={20} />
        {error}
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-dark-card rounded-lg w-1/3" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-32 bg-dark-card rounded-2xl" />)}
        </div>
        <div className="h-40 bg-dark-card rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div>
        <h1 className="text-3xl font-bold text-text-primary">Admin Dashboard</h1>
        <p className="text-text-secondary mt-1">Sistema de gestão e monitoramento</p>
      </div>

      {/* Overview Grid */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatsCard
            title="Total Usuários"
            value={overview.total_users.toString()}
            subtitle={`${overview.total_admins.toString()} admins`}
            icon={<Users size={24} />}
            variant="blue"
          />
          <StatsCard
            title="Usuários Ativos (7d)"
            value={overview.active_users_7d.toString()}
            subtitle={`24h: ${overview.active_users_24h.toString()}`}
            icon={<Activity size={24} />}
            variant="green"
          />
          <StatsCard
            title="Total Mensagens"
            value={overview.total_messages.toString()}
            subtitle={`~${(overview.total_messages / (overview.total_users || 1)).toFixed(1)}/user`}
            icon={<MessageSquare size={24} />}
            variant="purple"
          />
          <StatsCard
            title="Total Treinos"
            value={overview.total_workouts.toString()}
            subtitle={`${overview.total_nutrition_logs.toString()} logs de nutrição`}
            icon={<Dumbbell size={24} />}
            variant="orange"
          />
        </div>
      )}

      {/* Quality Metrics */}
      {metrics && (
        <div className="bg-dark-card border border-border rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-6">
            <TrendingUp className="text-gradient-start" size={24} />
            <h2 className="text-xl font-bold text-text-primary">Métricas de Qualidade</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="space-y-2">
              <p className="text-sm text-text-secondary">Mensagens por Usuário (média)</p>
              <p className="text-3xl font-bold text-text-primary">{metrics.avg_messages_per_user}</p>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-text-secondary">Engajamento em Treinos</p>
              <p className="text-3xl font-bold text-green-500">{metrics.workout_engagement_rate}%</p>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-text-secondary">Engajamento em Nutrição</p>
              <p className="text-3xl font-bold text-blue-500">{metrics.nutrition_engagement_rate}%</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
