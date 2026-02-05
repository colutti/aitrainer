import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminService } from '../../services/admin.service';

@Component({
  selector: 'app-admin-prompts',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="h-full overflow-y-auto p-6">
      <h1 class="text-3xl font-bold text-white mb-6">Prompts LLM</h1>

      <!-- Filter -->
      <input
        type="text"
        placeholder="Filtrar por email..."
        [(ngModel)]="userFilter"
        (input)="onFilterChange()"
        class="w-full p-3 bg-zinc-800 border border-zinc-700 rounded-lg text-white mb-6"
      />

      <!-- Prompts Accordion -->
      <div class="space-y-2">
        @for (prompt of prompts(); track prompt._id) {
          <div class="bg-zinc-800 border border-zinc-700 rounded-lg overflow-hidden">
            <button
              (click)="togglePrompt(prompt._id)"
              class="w-full p-4 text-left flex justify-between items-center hover:bg-zinc-750"
            >
              <div>
                <span class="font-semibold text-white">{{ prompt.user_email }}</span>
                <span class="text-sm text-zinc-400 ml-2">
                  {{ formatDate(prompt.timestamp) }}
                </span>
                <span class="text-xs text-zinc-500 ml-2 px-2 py-0.5 bg-zinc-700 rounded">
                  {{ getPromptTypeLabel(prompt.prompt?.type) }}
                </span>
              </div>
              <span class="text-zinc-400">
                {{ selectedPrompt() === prompt._id ? '▲' : '▼' }}
              </span>
            </button>

            @if (selectedPrompt() === prompt._id && promptDetails()) {
              <div class="p-4 border-t border-zinc-700 bg-zinc-900">
                <div class="mb-4 pb-2 border-b border-zinc-700">
                  <span class="text-xs text-zinc-500">Tipo:</span>
                  <span class="text-sm text-white ml-2">{{ getPromptTypeLabel(promptDetails()?.prompt?.type) }}</span>
                </div>

                <!-- Renderizar para prompts tipo "with_tools" (Chat) -->
                @if (promptDetails()?.prompt?.messages && promptDetails()?.prompt?.messages.length > 0) {
                  <div class="space-y-3">
                    @for (msg of promptDetails()?.prompt?.messages; track $index) {
                      <div class="bg-zinc-800 rounded p-3">
                        <div class="text-xs text-zinc-500 mb-2">{{ msg.role }}</div>
                        <div class="text-sm text-zinc-300 whitespace-pre-wrap font-mono break-words">
                          {{ msg.content }}
                        </div>
                      </div>
                    }
                  </div>
                }

                <!-- Renderizar para prompts tipo "simple" (Hero) -->
                @else if (promptDetails()?.prompt?.input) {
                  <div class="space-y-3">
                    @if (promptDetails()?.prompt?.input?.new_lines) {
                      <div class="bg-zinc-800 rounded p-3">
                        <div class="text-xs text-zinc-500 mb-2">Histórico de conversas</div>
                        <div class="text-sm text-zinc-300 whitespace-pre-wrap font-mono break-words">
                          {{ promptDetails()?.prompt?.input?.new_lines }}
                        </div>
                      </div>
                    }
                    @if (promptDetails()?.prompt?.input?.user_prompt_content) {
                      <div class="bg-zinc-800 rounded p-3">
                        <div class="text-xs text-zinc-500 mb-2">Análise de Metabolismo</div>
                        <div class="text-sm text-zinc-300 whitespace-pre-wrap font-mono break-words">
                          {{ promptDetails()?.prompt?.input?.user_prompt_content }}
                        </div>
                      </div>
                    }
                  </div>
                }

                <!-- Renderizar para prompts tipo V3 (String renderizada) -->
                @if (promptDetails()?.prompt?.prompt) {
                  <div class="mt-4">
                    <div class="text-xs text-zinc-500 mb-2 uppercase tracking-wider font-semibold">Prompt Renderizado Final:</div>
                    <div class="bg-zinc-800 rounded p-4 border border-zinc-700">
                      <div class="text-sm text-zinc-200 whitespace-pre-wrap font-mono break-all leading-relaxed">
                        {{ promptDetails().prompt.prompt }}
                      </div>
                    </div>
                  </div>
                }

                <!-- Fallback para prompts sem conteúdo reconhecido -->
                @else if (!promptDetails()?.prompt?.messages && !promptDetails()?.prompt?.input) {
                  <div class="text-sm text-zinc-500 italic p-4 bg-zinc-800/50 rounded border border-dashed border-zinc-700">
                     Este prompt parece estar vazio ou em um formato incompatível.
                  </div>
                }

              </div>
            }
          </div>
        }
      </div>

      @if (loading()) {
        <div class="flex justify-center py-12">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      }
    </div>
  `
})
export class AdminPromptsComponent implements OnInit {
  adminService = inject(AdminService);

  prompts = signal<any[]>([]);
  selectedPrompt = signal<string | null>(null);
  promptDetails = signal<any>(null);
  userFilter = '';
  loading = signal<boolean>(false);

  async ngOnInit() {
    await this.loadPrompts();
  }

  async loadPrompts() {
    this.loading.set(true);
    try {
      const result = await this.adminService.listPrompts(1, 20, this.userFilter || undefined);
      this.prompts.set(result.prompts);
    } catch (err) {
    } finally {
      this.loading.set(false);
    }
  }

  async onFilterChange() {
    await this.loadPrompts();
  }

  async togglePrompt(promptId: string) {
    if (this.selectedPrompt() === promptId) {
      this.selectedPrompt.set(null);
      this.promptDetails.set(null);
    } else {
      this.selectedPrompt.set(promptId);
      try {
        const details = await this.adminService.getPromptDetails(promptId);
        this.promptDetails.set(details);
      } catch (err) {
      }
    }
  }

  formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleString('pt-BR');
  }

  getPromptTypeLabel(type: string | undefined): string {
    if (!type) return 'Desconhecido';

    switch (type) {
      case 'simple':
        return 'Hero';
      case 'with_tools':
        return 'Chat';
      default:
        return type;
    }
  }
}
