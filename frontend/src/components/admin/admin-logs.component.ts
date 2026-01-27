import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AdminService } from '../../services/admin.service';

@Component({
  selector: 'app-admin-logs',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="h-full overflow-y-auto p-6">
      <h1 class="text-3xl font-bold text-white mb-6">Logs do Sistema</h1>

      <!-- Source Toggle -->
      <div class="mb-6 flex gap-2">
        <button
          (click)="setSource('local')"
          [class.bg-primary]="logSource() === 'local'"
          [class.bg-zinc-700]="logSource() !== 'local'"
          class="px-4 py-2 rounded hover:opacity-80"
        >
          📁 Logs Locais
        </button>
        <button
          (click)="setSource('betterstack')"
          [class.bg-primary]="logSource() === 'betterstack'"
          [class.bg-zinc-700]="logSource() !== 'betterstack'"
          class="px-4 py-2 rounded hover:opacity-80"
        >
          ☁️ BetterStack
        </button>
      </div>

      <!-- Logs Display -->
      <div class="bg-black border border-zinc-700 rounded-lg p-4 overflow-auto max-h-[600px]">
        <div class="font-mono text-xs text-zinc-300 space-y-1">
          @for (log of logs(); track $index) {
            <div>{{ log }}</div>
          }
        </div>
      </div>

      @if (loading()) {
        <div class="flex justify-center py-12">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      }

      @if (error()) {
        <div class="mt-4 bg-red-900/20 border border-red-700 rounded-lg p-4 text-red-400">
          {{ error() }}
        </div>
      }
    </div>
  `
})
export class AdminLogsComponent implements OnInit {
  adminService = inject(AdminService);

  logSource = signal<'local' | 'betterstack'>('local');
  logs = signal<string[]>([]);
  loading = signal<boolean>(false);
  error = signal<string | null>(null);

  async ngOnInit() {
    await this.loadLogs();
  }

  async setSource(source: 'local' | 'betterstack') {
    this.logSource.set(source);
    await this.loadLogs();
  }

  async loadLogs() {
    this.loading.set(true);
    this.error.set(null);

    try {
      if (this.logSource() === 'local') {
        const result = await this.adminService.getApplicationLogs(100);
        this.logs.set(result.logs);
      } else {
        const result = await this.adminService.getBetterStackLogs(100);
        this.logs.set(result.data?.map((d: any) => d.message) || []);
      }
    } catch (err: any) {
      console.error('Error loading logs:', err);
      this.error.set(err?.error?.detail || 'Erro ao carregar logs');
      this.logs.set([]);
    } finally {
      this.loading.set(false);
    }
  }
}
