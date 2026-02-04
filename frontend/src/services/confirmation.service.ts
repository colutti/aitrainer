import { Injectable, signal } from '@angular/core';

/**
 * Service for showing confirmation dialogs.
 * Uses native window.confirm() for now, but can be replaced with
 * a custom modal component in the future.
 */
@Injectable({
  providedIn: 'root'
})
export class ConfirmationService {
  /**
   * Shows a confirmation dialog and returns a promise with the user's choice.
   * @param message - The message to display
   * @param title - Optional title for the dialog
   * @returns Promise<boolean> - true if user clicked OK, false if Cancel
   */
  async confirm(message: string, title?: string): Promise<boolean> {
    const fullMessage = title ? `${title}\n\n${message}` : message;
    return window.confirm(fullMessage);
  }
}
