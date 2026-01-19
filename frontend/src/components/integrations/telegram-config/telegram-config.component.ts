import { Component, EventEmitter, OnInit, Output, inject, signal, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TelegramService } from '../../../services/telegram.service';
import { environment } from '../../../environment';

type ViewState = 'loading' | 'disconnected' | 'connected';

@Component({
  selector: 'app-telegram-config',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './telegram-config.component.html'
})
export class TelegramConfigComponent implements OnInit {
  @Output() close = new EventEmitter<void>();
  @Output() statusChanged = new EventEmitter<void>();
  
  private telegramService = inject(TelegramService);
  private cdr = inject(ChangeDetectorRef);
  
  viewState = signal<ViewState>('loading');
  errorMessage = signal<string>('');
  successMessage = signal<string>('');
  botUrl = environment.telegramBotUrl;
  
  // Connected state
  telegramUsername = signal<string | null>(null);
  linkedAt = signal<string | null>(null);
  
  // Code generation
  linkingCode = signal<string | null>(null);
  generatingCode = signal<boolean>(false);

  ngOnInit() {
    this.loadStatus();
  }

  async loadStatus() {
    this.viewState.set('loading');
    this.cdr.detectChanges();
    
    try {
      const status = await this.telegramService.getStatus();
      if (status.linked) {
        this.telegramUsername.set(status.telegram_username || null);
        this.linkedAt.set(status.linked_at || null);
        this.viewState.set('connected');
      } else {
        this.viewState.set('disconnected');
      }
    } catch (e) {
      console.error('Error loading Telegram status', e);
      this.viewState.set('disconnected');
    } finally {
      this.cdr.detectChanges();
    }
  }

  async generateCode() {
    this.generatingCode.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');
    this.cdr.detectChanges();
    
    try {
      const result = await this.telegramService.generateCode();
      this.linkingCode.set(result.code);
      this.successMessage.set('Código gerado! Válido por 10 minutos.');
    } catch (e) {
      console.error('Error generating code', e);
      this.errorMessage.set('Erro ao gerar código.');
    } finally {
      this.generatingCode.set(false);
      this.cdr.detectChanges();
    }
  }

  copyCode() {
    const code = this.linkingCode();
    if (!code) return;
    
    navigator.clipboard.writeText(code).then(() => {
      this.successMessage.set('Código copiado!');
      setTimeout(() => this.successMessage.set(''), 2000);
      this.cdr.detectChanges();
    });
  }

  async unlink() {
    if (!confirm('Tem certeza que deseja desvincular sua conta do Telegram?')) return;
    
    try {
      this.viewState.set('loading');
      this.cdr.detectChanges();
      
      await this.telegramService.unlink();
      
      this.linkingCode.set(null);
      this.telegramUsername.set(null);
      this.linkedAt.set(null);
      this.viewState.set('disconnected');
      this.statusChanged.emit();
      this.successMessage.set('Conta desvinculada.');
    } catch (e) {
      console.error('Error unlinking', e);
      this.errorMessage.set('Erro ao desvincular.');
      this.viewState.set('connected');
    } finally {
      this.cdr.detectChanges();
    }
  }

  closeModal() {
    this.close.emit();
  }
}
