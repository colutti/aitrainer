import { Component, OnInit, inject, signal, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HevyService } from '../../services/hevy.service';
import { TelegramService } from '../../services/telegram.service';
import { IntegrationProvider } from '../../models/integration.model';
import { IntegrationCardComponent } from './integration-card/integration-card.component';
import { HevyConfigComponent } from './hevy-config/hevy-config.component';
import { MfpImportComponent } from './mfp-import/mfp-import.component';
import { ZeppLifeImportComponent } from './zepp-life-import/zepp-life-import.component';
import { TelegramConfigComponent } from './telegram-config/telegram-config.component';

@Component({
  selector: 'app-integrations',
  standalone: true,
  imports: [CommonModule, IntegrationCardComponent, HevyConfigComponent, MfpImportComponent, ZeppLifeImportComponent, TelegramConfigComponent],
  templateUrl: './integrations.component.html'
})
export class IntegrationsComponent implements OnInit {
  private hevyService = inject(HevyService);
  private telegramService = inject(TelegramService);
  private cdr = inject(ChangeDetectorRef);
  
  hevyProvider = signal<IntegrationProvider>({ 
    id: 'hevy', 
    name: 'Hevy', 
    description: 'Sincronize treinos e progresso.', 
    status: 'disconnected', 
    isEnabled: false 
  });

  telegramProvider = signal<IntegrationProvider>({ 
    id: 'telegram', 
    name: 'Telegram', 
    description: 'Converse com a IA pelo Telegram.', 
    status: 'disconnected', 
    isEnabled: true 
  });

  importTools = signal<IntegrationProvider[]>([
    { id: 'mfp', name: 'MyFitnessPal', description: 'Importe seu histórico nutricional.', status: 'disconnected', isEnabled: true },
    { id: 'zepp-life', name: 'Zepp Life', description: 'Importe seu histórico de peso.', status: 'disconnected', isEnabled: true },
  ]);
  
  showHevyConfig = signal<boolean>(false);
  showMfpImport = signal<boolean>(false);
  showZeppLifeImport = signal<boolean>(false);
  showTelegramConfig = signal<boolean>(false);

  ngOnInit() {
    this.refreshHevyStatus();
    this.refreshTelegramStatus();
  }

  async refreshHevyStatus() {
    try {
      const status = await this.hevyService.getStatus();
      
      let newStatus: 'connected' | 'paused' | 'disconnected' = 'disconnected';
      if (status.hasKey) {
        newStatus = status.enabled ? 'connected' : 'paused';
      }

      this.hevyProvider.set({
        ...this.hevyProvider(),
        isEnabled: status.enabled,
        status: newStatus
      });
      
      this.cdr.detectChanges();
    } catch (e) {
    }
  }

  async refreshTelegramStatus() {
    try {
      const status = await this.telegramService.getStatus();
      const newStatus = status.linked ? 'connected' : 'disconnected';
      this.telegramProvider.set({
        ...this.telegramProvider(),
        status: newStatus
      });
      this.cdr.detectChanges();
    } catch (e) {
    }
  }

  openConfig(providerId: string) {
    if (providerId === 'hevy') {
      this.showHevyConfig.set(true);
    } else if (providerId === 'mfp') {
      this.showMfpImport.set(true);
    } else if (providerId === 'zepp-life') {
      this.showZeppLifeImport.set(true);
    } else if (providerId === 'telegram') {
      this.showTelegramConfig.set(true);
    }
    this.cdr.detectChanges();
  }

  onMfpImportClose() {
    this.showMfpImport.set(false);
    this.cdr.detectChanges();
  }

  onZeppLifeImportClose() {
    this.showZeppLifeImport.set(false);
    this.cdr.detectChanges();
  }

  onHevyConfigClose() {
    this.showHevyConfig.set(false);
    this.refreshHevyStatus();
  }

  onHevyStatusChanged() {
    // When Config modal says something changed (connect/disconnect/import)
    this.refreshHevyStatus();
  }

  onTelegramConfigClose() {
    this.showTelegramConfig.set(false);
    this.refreshTelegramStatus();
  }

  onTelegramStatusChanged() {
    this.refreshTelegramStatus();
  }
}
