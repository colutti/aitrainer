import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AdminService } from '../../services/admin.service';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="h-full overflow-y-auto p-6">
      <div class="mb-6">
        <h1 class="text-3xl font-bold text-white">Admin Dashboard</h1>
        <p class="text-zinc-400 mt-1">Sistema de gestão e monitoramento</p>
      </div>

      <!-- KPI Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <!-- Total Users -->
        <div class="bg-zinc-800 border border-zinc-700 rounded-lg p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-zinc-400">Total Usuários</p>
              <p class="text-3xl font-bold text-white mt-1">
                {{ overview()?.total_users || 0 }}
              </p>
              <p class="text-xs text-zinc-500 mt-1">
                {{ overview()?.total_admins || 0 }} admin(s)
              </p>
            </div>
            <div class="text-4xl">👥</div>
          </div>
        </div>

        <!-- Active Users -->
        <div class="bg-zinc-800 border border-zinc-700 rounded-lg p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-zinc-400">Ativos Recentemente</p>
              <p class="text-3xl font-bold text-green-500 mt-1">
                {{ overview()?.active_users_7d || 0 }}
              </p>
              <p class="text-xs text-zinc-500 mt-1">
                7 dias: {{ overview()?.active_users_7d || 0 }} | 24h: {{ overview()?.active_users_24h || 0 }}
              </p>
            </div>
            <div class="text-4xl">✅</div>
          </div>
        </div>

        <!-- Total Messages -->
        <div class="bg-zinc-800 border border-zinc-700 rounded-lg p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-zinc-400">Total Mensagens</p>
              <p class="text-3xl font-bold text-blue-500 mt-1">
                {{ overview()?.total_messages || 0 }}
              </p>
              <p class="text-xs text-zinc-500 mt-1">
                ~{{ (overview()?.total_messages / overview()?.total_users || 0).toFixed(1) }} por usuário
              </p>
            </div>
            <div class="text-4xl">💬</div>
          </div>
        </div>

        <!-- Total Workouts -->
        <div class="bg-zinc-800 border border-zinc-700 rounded-lg p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-zinc-400">Total Treinos</p>
              <p class="text-3xl font-bold text-orange-500 mt-1">
                {{ overview()?.total_workouts || 0 }}
              </p>
              <p class="text-xs text-zinc-500 mt-1">
                {{ overview()?.total_nutrition_logs || 0 }} logs de nutrição
              </p>
            </div>
            <div class="text-4xl">🏋️</div>
          </div>
        </div>
      </div>

      <!-- Quality Metrics -->
      @if (qualityMetrics()) {
        <div class="bg-zinc-800 border border-zinc-700 rounded-lg p-6 mb-6">
          <h2 class="text-xl font-bold text-white mb-4">Métricas de Qualidade</h2>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p class="text-sm text-zinc-400">Mensagens por Usuário (média)</p>
              <p class="text-2xl font-bold text-white mt-1">
                {{ qualityMetrics()?.avg_messages_per_user || 0 }}
              </p>
            </div>

            <div>
              <p class="text-sm text-zinc-400">Taxa de Engajamento (Treinos)</p>
              <p class="text-2xl font-bold text-white mt-1">
                {{ qualityMetrics()?.workout_engagement_rate || 0 }}%
              </p>
            </div>

            <div>
              <p class="text-sm text-zinc-400">Taxa de Engajamento (Nutrição)</p>
              <p class="text-2xl font-bold text-white mt-1">
                {{ qualityMetrics()?.nutrition_engagement_rate || 0 }}%
              </p>
            </div>
          </div>
        </div>
      }

      @if (loading()) {
        <div class="flex items-center justify-center py-12">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      }

      @if (error()) {
        <div class="bg-red-900/20 border border-red-700 rounded-lg p-4 text-red-400">
          ⚠️ Erro ao carregar dados: {{ error() }}
        </div>
      }
    </div>
  `,
  styles: []
})
export class AdminDashboardComponent implements OnInit {
  adminService = inject(AdminService);

  overview = signal<any>(null);
  qualityMetrics = signal<any>(null);
  loading = signal<boolean>(true);
  error = signal<string | null>(null);

  async ngOnInit() {
    try {
      this.loading.set(true);
      this.error.set(null);

      const [overviewData, metricsData] = await Promise.all([
        this.adminService.getOverview(),
        this.adminService.getQualityMetrics()
      ]);

      this.overview.set(overviewData);
      this.qualityMetrics.set(metricsData);
    } catch (err: any) {
      this.error.set(err?.error?.detail || 'Falha ao carregar dados');
    } finally {
      this.loading.set(false);
    }
  }
}
