import { Injectable, signal } from '@angular/core';

export interface ConfirmationConfig {
  message: string;
  title?: string;
  confirmText?: string;
  cancelText?: string;
}

@Injectable({ providedIn: 'root' })
export class ConfirmationService {
  isVisible = signal(false);
  config = signal<ConfirmationConfig | null>(null);
  private resolver: ((value: boolean) => void) | null = null;

  confirm(config: string | ConfirmationConfig): Promise<boolean> {
    const fullConfig: ConfirmationConfig =
      typeof config === 'string'
        ? { message: config }
        : config;

    this.config.set(fullConfig);
    this.isVisible.set(true);

    return new Promise<boolean>((resolve) => {
      this.resolver = resolve;
    });
  }

  onConfirm(): void {
    this.resolver?.(true);
    this.close();
  }

  onCancel(): void {
    this.resolver?.(false);
    this.close();
  }

  private close(): void {
    this.isVisible.set(false);
    this.config.set(null);
    this.resolver = null;
  }
}
