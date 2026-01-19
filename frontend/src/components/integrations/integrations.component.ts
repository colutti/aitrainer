import { Component, OnInit, inject, signal, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HevyService } from '../../services/hevy.service';
import { IntegrationProvider } from '../../models/integration.model';
import { IntegrationCardComponent } from './integration-card/integration-card.component';
import { HevyConfigComponent } from './hevy-config/hevy-config.component';
import { MfpImportComponent } from './mfp-import/mfp-import.component';

@Component({
  selector: 'app-integrations',
  standalone: true,
  imports: [CommonModule, IntegrationCardComponent, HevyConfigComponent, MfpImportComponent],
  templateUrl: './integrations.component.html'
})
export class IntegrationsComponent implements OnInit {
  private hevyService = inject(HevyService);
  private cdr = inject(ChangeDetectorRef);
  
  hevyProvider = signal<IntegrationProvider>({ 
    id: 'hevy', 
    name: 'Hevy', 
    description: 'Sincronize treinos e progresso.', 
    status: 'disconnected', 
    isEnabled: false 
  });

  otherProviders = signal<IntegrationProvider[]>([
    { id: 'mfp', name: 'MyFitnessPal', description: 'Importe seu histórico nutricional.', status: 'disconnected', isEnabled: true },
  ]);
  
  showHevyConfig = signal<boolean>(false);
  showMfpImport = signal<boolean>(false);

  ngOnInit() {
    this.refreshHevyStatus();
  }

  async refreshHevyStatus() {
    console.log('Integrations: refreshing Hevy status...');
    try {
      const status = await this.hevyService.getStatus();
      console.log('Integrations: Status received', status);
      
      let newStatus: 'connected' | 'paused' | 'disconnected' = 'disconnected';
      if (status.hasKey) {
        newStatus = status.enabled ? 'connected' : 'paused';
      }

      this.hevyProvider.set({
        ...this.hevyProvider(),
        isEnabled: status.enabled,
        status: newStatus
      });
      
      console.log('Integrations: New provider state', this.hevyProvider());
      this.cdr.detectChanges();
    } catch (e) {
      console.error('Integrations: load error', e);
    }
  }

  openConfig(providerId: string) {
    if (providerId === 'hevy') {
      this.showHevyConfig.set(true);
    } else if (providerId === 'mfp') {
      this.showMfpImport.set(true);
    }
    this.cdr.detectChanges();
  }

  onMfpImportClose() {
    this.showMfpImport.set(false);
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
}
