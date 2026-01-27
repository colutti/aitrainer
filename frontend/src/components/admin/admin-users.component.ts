import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminService } from '../../services/admin.service';
import { NotificationService } from '../../services/notification.service';

@Component({
  selector: 'app-admin-users',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="h-full overflow-y-auto p-6">
      <h1 class="text-3xl font-bold text-white mb-6">Gestão de Usuários</h1>

      <!-- Search Bar -->
      <div class="mb-6">
        <input
          type="text"
          placeholder="Buscar por email..."
          [(ngModel)]="searchQuery"
          (input)="onSearchChange()"
          class="w-full p-3 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
        />
      </div>

      <!-- Users Table -->
      <div class="bg-zinc-800 border border-zinc-700 rounded-lg overflow-hidden">
        <table class="w-full">
          <thead class="bg-zinc-900">
            <tr class="text-left text-zinc-400 text-sm">
              <th class="p-4">Email</th>
              <th class="p-4">Idade</th>
              <th class="p-4">Objetivo</th>
              <th class="p-4">Role</th>
              <th class="p-4">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-700">
            @for (user of users(); track user.email) {
              <tr class="hover:bg-zinc-750 transition-colors">
                <td class="p-4 text-white font-medium">{{ user.email }}</td>
                <td class="p-4 text-zinc-300">{{ user.age || 'N/A' }}</td>
                <td class="p-4 text-zinc-300">{{ user.goal_type || 'N/A' }}</td>
                <td class="p-4">
                  <span 
                    class="px-2 py-1 rounded-full text-xs font-bold"
                    [class]="user.role === 'admin' ? 'bg-yellow-500/20 text-yellow-500' : 'bg-zinc-700 text-zinc-300'"
                  >
                    {{ user.role | uppercase }}
                  </span>
                </td>
                <td class="p-4">
                  <div class="flex items-center space-x-3">
                    <button 
                      (click)="viewUser(user)" 
                      class="text-blue-400 hover:text-blue-300 transition-colors text-sm font-semibold"
                    >
                      Ver
                    </button>
                    @if (user.role !== 'admin') {
                      <button 
                        (click)="deleteUser(user)" 
                        class="text-red-400 hover:text-red-300 transition-colors text-sm font-semibold"
                      >
                        Deletar
                      </button>
                    } @else {
                      <span class="text-zinc-600 text-sm cursor-not-allowed" title="Administradores não podem ser deletados">
                        Deletar
                      </span>
                    }
                  </div>
                </td>
              </tr>
            }
            @if (users().length === 0 && !loading()) {
              <tr>
                <td colspan="5" class="p-12 text-center text-zinc-500">
                  Nenhum usuário encontrado.
                </td>
              </tr>
            }
          </tbody>
        </table>

        <!-- Pagination -->
        <div class="flex justify-center gap-2 p-4 bg-zinc-900 border-t border-zinc-700">
          @for (p of paginationArray(); track $index) {
            <button
              (click)="goToPage($index + 1)"
              [class.bg-primary]="currentPage() === $index + 1"
              [class.bg-zinc-700]="currentPage() !== $index + 1"
              class="px-3 py-1 rounded hover:bg-primary/80 transition-colors text-white text-sm"
            >
              {{ $index + 1 }}
            </button>
          }
        </div>
      </div>

      @if (loading()) {
        <div class="flex justify-center py-12">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      }

      <!-- Quick Details Modal-like (Optional implementation) -->
      @if (selectedUserDetails()) {
        <div class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100] p-4" (click)="selectedUserDetails.set(null)">
          <div class="bg-zinc-900 border border-zinc-700 p-6 rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto" (click)="$event.stopPropagation()">
            <div class="flex justify-between items-center mb-6">
              <h2 class="text-2xl font-bold text-white">Detalhes do Usuário</h2>
              <button (click)="selectedUserDetails.set(null)" class="text-zinc-400 hover:text-white">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <pre class="bg-black/40 p-4 rounded-lg text-green-400 text-sm overflow-x-auto">{{ selectedUserDetails() | json }}</pre>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    :host { display: block; height: 100%; }
  `]
})
export class AdminUsersComponent implements OnInit {
  adminService = inject(AdminService);
  notificationService = inject(NotificationService);

  users = signal<any[]>([]);
  totalPages = signal<number>(0);
  currentPage = signal<number>(1);
  searchQuery = '';
  loading = signal<boolean>(false);
  selectedUserDetails = signal<any | null>(null);

  paginationArray() {
    return Array(this.totalPages()).fill(0);
  }

  async ngOnInit() {
    await this.loadUsers();
  }

  async loadUsers() {
    this.loading.set(true);
    try {
      const result = await this.adminService.listUsers(
        this.currentPage(),
        20,
        this.searchQuery || undefined
      );
      this.users.set(result.users);
      this.totalPages.set(result.total_pages);
    } catch (err) {
      console.error('Error loading users:', err);
      this.notificationService.error('Erro ao carregar lista de usuários');
    } finally {
      this.loading.set(false);
    }
  }

  async onSearchChange() {
    this.currentPage.set(1);
    await this.loadUsers();
  }

  async goToPage(page: number) {
    this.currentPage.set(page);
    await this.loadUsers();
  }

  async viewUser(user: any) {
    try {
      this.notificationService.info(`Buscando detalhes de ${user.email}...`);
      const details = await this.adminService.getUserDetails(user.email);
      this.selectedUserDetails.set(details);
    } catch (err) {
      console.error('View user error:', err);
      this.notificationService.error('Erro ao buscar detalhes do usuário');
    }
  }

  async deleteUser(user: any) {
    if (user.role === 'admin') {
      this.notificationService.error('Não é possível deletar usuários administradores.');
      return;
    }

    if (!window.confirm(`Deseja realmente deletar o usuário ${user.email}? Esta ação removerá permanentemente todos os seus dados e memórias.`)) {
      return;
    }

    try {
      this.notificationService.info('Deletando usuário...');
      await this.adminService.deleteUser(user.email);
      this.notificationService.success('Usuário deletado com sucesso');
      await this.loadUsers();
    } catch (err: any) {
      console.error('Delete user error:', err);
      const msg = err?.error?.detail || 'Erro ao deletar usuário';
      this.notificationService.error(msg);
    }
  }
}

