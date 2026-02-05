import { Component, EventEmitter, OnInit, Output, inject, signal, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HevyService } from '../../../services/hevy.service';
import { AppDateFormatPipe } from '../../../pipes/date-format.pipe';

type ViewState = 'loading' | 'setup' | 'connected' | 'confirm_disconnect';

@Component({
  selector: 'app-hevy-config',
  standalone: true,
  imports: [CommonModule, FormsModule, AppDateFormatPipe],
  templateUrl: './hevy-config.component.html'
})
export class HevyConfigComponent implements OnInit {
  @Output() close = new EventEmitter<void>();
  @Output() statusChanged = new EventEmitter<void>();
  
  private hevyService = inject(HevyService);
  private cdr = inject(ChangeDetectorRef);
  
  viewState = signal<ViewState>('loading');
  errorMessage = signal<string>('');
  successMessage = signal<string>('');
  
  // Setup
  apiKeyInput = '';
  validating = signal<boolean>(false);
  
  // Connected
  maskedKey = signal<string>('');
  workoutCount = signal<number>(0);
  lastSync = signal<string | null>(null);
  
  // Import
  importDateDisplay = '01/01/2025';
  importMode = 'skip_duplicates';
  importing = signal<boolean>(false);
  importResult = signal<{ imported: number; skipped: number; failed: number } | null>(null);

  /**
   * Converts DD/MM/YYYY string to YYYY-MM-DD
   */
  private parseDisplayDate(dateStr: string): string {
    const parts = dateStr.split('/');
    if (parts.length !== 3) return new Date().toISOString().split('T')[0];
    const [day, month, year] = parts;
    return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
  }

  ngOnInit() {
    this.loadStatus();
  }

  async loadStatus() {
    this.viewState.set('loading');
    this.cdr.detectChanges();
    
    try {
      const status = await this.hevyService.getStatus();
      if (status.hasKey) {
        this.maskedKey.set(status.apiKeyMasked || '****');
        this.lastSync.set(status.lastSync || null);
        this.viewState.set('connected');
        this.loadCount();
        this.loadWebhookConfig();
      } else {
        this.resetInternalState();
        this.viewState.set('setup');
      }
    } catch {
      this.resetInternalState();
      this.viewState.set('setup');
    } finally {
      this.cdr.detectChanges();
    }
  }

  private resetInternalState() {
    this.maskedKey.set('');
    this.workoutCount.set(0);
    this.lastSync.set(null);
    this.importResult.set(null);
    this.successMessage.set('');
  }

  private async loadCount() {
    try {
      const count = await this.hevyService.getCount();
      this.workoutCount.set(count);
      this.cdr.detectChanges();
    } catch {
      // Ignore count fetch errors 
    }
  }

  async validateAndConnect() {
    if (!this.apiKeyInput.trim()) return;
    this.validating.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');
    this.cdr.detectChanges();
    
    try {
      const result = await this.hevyService.validateKey(this.apiKeyInput);
      if (result.valid) {
        await this.hevyService.saveConfig(this.apiKeyInput, true);
        this.apiKeyInput = '';
        this.statusChanged.emit();
        await this.loadStatus();
        this.successMessage.set('Conectado com sucesso!');
      } else {
        this.errorMessage.set('Chave inválida.');
      }
    } catch {
      this.errorMessage.set('Erro ao conectar.');
    } finally {
      this.validating.set(false);
      this.cdr.detectChanges();
    }
  }

  // Webhook
  webhookUrl = signal<string | null>(null);
  webhookAuthHeader = signal<string | null>(null);
  generatingWebhook = signal<boolean>(false);
  showFullAuth = signal<boolean>(false);

  async loadWebhookConfig() {
    try {
      const config = await this.hevyService.getWebhookConfig();
      this.webhookUrl.set(config.webhook_url || null);
      this.webhookAuthHeader.set(config.auth_header || null);
      this.showFullAuth.set(false);
    } catch (error) {
    }
  }

  async generateWebhook() {
    this.generatingWebhook.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');
    this.cdr.detectChanges();
    
    try {
      const creds = await this.hevyService.generateWebhook();
      this.webhookUrl.set(creds.webhook_url);
      this.webhookAuthHeader.set(creds.auth_header);
      this.showFullAuth.set(true);
      this.successMessage.set('Webhook configurado! Copie o segredo agora.');
    } catch {
      this.errorMessage.set('Erro ao gerar webhook.');
    } finally {
      this.generatingWebhook.set(false);
      this.cdr.detectChanges();
    }
  }

  async revokeWebhook() {
    if (!confirm('Tem certeza que deseja revogar o webhook? A sincronização automática irá parar.')) return;
    
    try {
      await this.hevyService.revokeWebhook();
      this.webhookUrl.set(null);
      this.webhookAuthHeader.set(null);
      this.showFullAuth.set(false);
      this.successMessage.set('Webhook revogado.');
    } catch {
      this.errorMessage.set('Erro ao revogar webhook.');
    } finally {
      this.cdr.detectChanges();
    }
  }

  copyToClipboard(text: string, label: string) {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
      this.successMessage.set(`${label} copiado!`);
      setTimeout(() => this.successMessage.set(''), 2000);
      this.cdr.detectChanges();
    });
  }

  startDisconnect() {
    this.viewState.set('confirm_disconnect');
    this.cdr.detectChanges();
  }

  cancelDisconnect() {
    this.viewState.set('connected');
    this.cdr.detectChanges();
  }

  async confirmDisconnect() {
    try {
      this.viewState.set('loading');
      this.cdr.detectChanges();

      await this.hevyService.saveConfig('', false);
      
      this.resetInternalState();
      this.viewState.set('setup');
      this.statusChanged.emit();
    } catch {
      this.errorMessage.set('Erro ao desconectar.');
      this.viewState.set('connected');
    } finally {
      this.cdr.detectChanges();
    }
  }

  async runImport() {
    this.importing.set(true);
    this.importResult.set(null);
    this.errorMessage.set('');
    this.successMessage.set('');
    this.cdr.detectChanges();
    
    try {
      const fromDateIso = this.parseDisplayDate(this.importDateDisplay);
      const res = await this.hevyService.importWorkouts(fromDateIso, this.importMode as 'skip_duplicates' | 'overwrite');
      this.importResult.set(res);
      this.statusChanged.emit();
      
      if (res.imported > 0) {
        this.successMessage.set(`${res.imported} treinos importados com sucesso!`);
      } else if (res.skipped > 0) {
        this.successMessage.set('Nenhum treino novo. Alguns foram pulados por já existirem.');
      } else {
        this.successMessage.set('Sincronização concluída. Nenhum treino novo encontrado.');
      }

      await this.loadStatus();
    } catch {
      this.errorMessage.set('Erro na importação.');
    } finally {
      this.importing.set(false);
      this.cdr.detectChanges();
    }
  }

  closeModal() {
    this.close.emit();
  }
}
