import { Component, inject } from '@angular/core';
import { ConfirmationService } from '../../../services/confirmation.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-confirmation-modal',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (confirmationService.isVisible()) {
      <div class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
        <div class="bg-light-bg rounded-2xl border border-secondary shadow-2xl max-w-md w-full p-6 space-y-4 animate-in fade-in zoom-in duration-200">
          <h3 class="text-xl font-bold text-text-primary">
            {{ confirmationService.config()?.title || 'Confirmar' }}
          </h3>
          <p class="text-text-secondary">
            {{ confirmationService.config()?.message }}
          </p>
          <div class="flex gap-3">
            <button
              (click)="confirmationService.onCancel()"
              class="flex-1 px-4 py-2 rounded-lg bg-secondary hover:bg-secondary/80 text-white transition-colors">
              {{ confirmationService.config()?.cancelText || 'Cancelar' }}
            </button>
            <button
              (click)="confirmationService.onConfirm()"
              class="flex-1 px-4 py-2 rounded-lg bg-primary hover:bg-primary/80 text-white transition-colors">
              {{ confirmationService.config()?.confirmText || 'Confirmar' }}
            </button>
          </div>
        </div>
      </div>
    }
  `
})
export class ConfirmationModalComponent {
  confirmationService = inject(ConfirmationService);
}
