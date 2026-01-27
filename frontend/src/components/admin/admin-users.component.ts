import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminService } from '../../services/admin.service';

@Component({
  selector: 'app-admin-users',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="h-full overflow-y-auto p-6">
      <h1 class="text-3xl font-bold text-white mb-6">Gestão de Usuários</h1>

      <!-- Search Bar -->
      <input
        type="text"
        placeholder="Buscar por email..."
        [(ngModel)]="searchQuery"
        (input)="onSearchChange()"
        class="w-full p-3 bg-zinc-800 border border-zinc-700 rounded-lg text-white mb-6"
      />

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
              <tr class="hover:bg-zinc-750">
                <td class="p-4 text-white">{{ user.email }}</td>
                <td class="p-4 text-zinc-300">{{ user.age }}</td>
                <td class="p-4 text-zinc-300">{{ user.goal_type }}</td>
                <td class="p-4">
                  <span [class]="user.role === 'admin' ? 'text-yellow-500' : 'text-zinc-400'">
                    {{ user.role }}
                  </span>
                </td>
                <td class="p-4">
                  <button (click)="viewUser(user.email)" class="text-blue-500 hover:underline mr-3">
                    Ver
                  </button>
                  <button (click)="deleteUser(user.email)" class="text-red-500 hover:underline">
                    Deletar
                  </button>
                </td>
              </tr>
            }
          </tbody>
        </table>

        <!-- Pagination -->
        <div class="flex justify-center gap-2 p-4 bg-zinc-900">
          @for (p of paginationArray(); track $index) {
            <button
              (click)="goToPage($index + 1)"
              [class.bg-primary]="currentPage() === $index + 1"
              [class.bg-zinc-700]="currentPage() !== $index + 1"
              class="px-3 py-1 rounded hover:bg-primary/80"
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
    </div>
  `
})
export class AdminUsersComponent implements OnInit {
  adminService = inject(AdminService);

  users = signal<any[]>([]);
  totalPages = signal<number>(0);
  currentPage = signal<number>(1);
  searchQuery = '';
  loading = signal<boolean>(false);

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

  async viewUser(email: string) {
    try {
      const details = await this.adminService.getUserDetails(email);
      alert(JSON.stringify(details, null, 2));
    } catch (err) {
      alert('Erro ao buscar detalhes');
    }
  }

  async deleteUser(email: string) {
    if (!confirm(`Deletar usuário ${email}? Esta ação é irreversível!`)) return;

    try {
      await this.adminService.deleteUser(email);
      alert('Usuário deletado com sucesso');
      await this.loadUsers();
    } catch (err: any) {
      alert(err?.error?.detail || 'Erro ao deletar usuário');
    }
  }
}
