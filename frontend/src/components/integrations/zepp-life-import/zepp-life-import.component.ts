import { Component, EventEmitter, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WeightService } from '../../../services/weight.service';

@Component({
  selector: 'app-zepp-life-import',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './zepp-life-import.component.html',
  styles: [`
    .drag-drop-zone {
      border: 2px dashed var(--color-border);
      border-radius: 12px;
      padding: 2rem;
      text-align: center;
      transition: all 0.2s;
      cursor: pointer;
    }
    .drag-drop-zone:hover, .drag-drop-zone.drag-over {
      border-color: var(--color-primary);
      background: rgba(var(--color-primary-rgb), 0.05);
    }
    .file-input {
      display: none;
    }
    .btn-primary {
      background: var(--color-primary);
      color: white;
      border: none;
      padding: 0.75rem 1.5rem;
      border-radius: 8px;
      font-weight: 500;
      cursor: pointer;
      transition: opacity 0.2s;
    }
    .btn-primary:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    .status-box {
      margin-top: 1.5rem;
      padding: 1rem;
      border-radius: 8px;
      background: var(--color-surface-dim);
    }
    .success { color: var(--color-success); }
    .error { color: var(--color-error); }
  `]
})
export class ZeppLifeImportComponent {
  @Output() close = new EventEmitter<void>();
  
  error = signal<string | null>(null);
  result = signal<any>(null);
  selectedFile = signal<File | null>(null);
  isUploading = signal<boolean>(false);
  isDragOver = signal<boolean>(false);

  constructor(private weightService: WeightService) {}

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.isDragOver.set(true);
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    this.isDragOver.set(false);
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragOver.set(false);
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.validateAndSelectFile(files[0]);
    }
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.validateAndSelectFile(input.files[0]);
    }
  }

  validateAndSelectFile(file: File) {
    if (!file.name.endsWith('.csv')) {
      this.error.set('Por favor selecione um arquivo CSV.');
      this.selectedFile.set(null);
      return;
    }
    this.selectedFile.set(file);
    this.error.set(null);
    this.result.set(null);
  }

  async upload() {
    const file = this.selectedFile();
    if (!file) return;

    this.isUploading.set(true);
    this.error.set(null);

    try {
      const res = await this.weightService.importZeppLifeData(file);
      this.result.set(res);
    } catch (err: any) {
      this.error.set(err.error?.detail || 'Falha ao importar dados. Tente novamente.');
    } finally {
      this.isUploading.set(false);
    }
  }
}
