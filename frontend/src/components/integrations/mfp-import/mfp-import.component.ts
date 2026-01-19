import { Component, EventEmitter, Output, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ImportService } from '../../../services/import.service';
import { ImportResult } from '../../../models/integration.model';

type ViewState = 'setup' | 'importing' | 'success';

@Component({
  selector: 'app-mfp-import',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './mfp-import.component.html'
})
export class MfpImportComponent {
  @Output() close = new EventEmitter<void>();
  @Output() importCompleted = new EventEmitter<void>();

  private importService = inject(ImportService);

  viewState = signal<ViewState>('setup');
  errorMessage = signal<string>('');
  selectedFile = signal<File | null>(null);
  importResult = signal<ImportResult | null>(null);
  showInstructions = signal<boolean>(true);

  toggleInstructions() {
    this.showInstructions.update(v => !v);
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const file = input.files[0];
      if (file.name.endsWith('.csv')) {
        this.selectedFile.set(file);
        this.errorMessage.set('');
      } else {
        this.errorMessage.set('Por favor, selecione um arquivo .csv');
        this.selectedFile.set(null);
      }
    }
  }

  uploadFile() {
    const file = this.selectedFile();
    if (!file) return;

    this.viewState.set('importing');
    this.errorMessage.set('');

    this.importService.uploadMyFitnessPalCSV(file).subscribe({
      next: (result) => {
        this.importResult.set(result);
        this.viewState.set('success');
        this.importCompleted.emit();
      },
      error: (err) => {
        console.error('Import error', err);
        this.errorMessage.set(err.error?.detail || 'Falha na importação. Verifique o arquivo.');
        this.viewState.set('setup');
      }
    });
  }

  reset() {
    this.viewState.set('setup');
    this.selectedFile.set(null);
    this.importResult.set(null);
    this.errorMessage.set('');
  }

  closeModal() {
    this.close.emit();
  }
}
