import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IntegrationProvider } from '../../../models/integration.model';

@Component({
  selector: 'app-integration-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './integration-card.component.html'
})
export class IntegrationCardComponent {
  @Input({ required: true }) provider!: IntegrationProvider;
  @Output() configure = new EventEmitter<void>();

  onCardClick() {
    if (this.provider.status !== 'coming_soon') {
      this.configure.emit();
    }
  }
}
