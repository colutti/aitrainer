import { Component, EventEmitter, OnInit, Output, inject, signal, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HevyService } from '../../../services/hevy.service';

type ViewState = 'loading' | 'setup' | 'connected' | 'confirm_disconnect';

@Component({
  selector: 'app-hevy-config',
  standalone: true,
  imports: [CommonModule, FormsModule],
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
  importDate = '2025-01-01';
  importMode = 'skip_duplicates';
  importing = signal<boolean>(false);
  importResult = signal<{ imported: number; skipped: number; failed: number } | null>(null);

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
      } else {
        this.resetInternalState();
        this.viewState.set('setup');
      }
    } catch (e) {
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
    } catch { }
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
    } catch (e) {
      this.errorMessage.set('Erro ao conectar.');
    } finally {
      this.validating.set(false);
      this.cdr.detectChanges();
    }
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
    } catch (e) {
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
      const res = await this.hevyService.importWorkouts(this.importDate, this.importMode as any);
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
    } catch (e) {
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
