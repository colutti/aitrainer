import { Component, OnInit, inject, signal, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HevyService } from '../../services/hevy.service';
import { IntegrationProvider } from '../../models/integration.model';
import { IntegrationCardComponent } from './integration-card/integration-card.component';
import { HevyConfigComponent } from './hevy-config/hevy-config.component';

@Component({
  selector: 'app-integrations',
  standalone: true,
  imports: [CommonModule, IntegrationCardComponent, HevyConfigComponent],
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
    { id: 'mfp', name: 'MyFitnessPal', description: 'Acompanhe nutrição e calorias.', status: 'coming_soon', isEnabled: false },
  ]);
  
  showHevyConfig = signal<boolean>(false);

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
      this.cdr.detectChanges();
    }
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
