import { Injectable, signal } from '@angular/core';

/** Available views in the application */
export type View = 'chat' | 'user-profile' | 'trainer-settings' | 'memories';

/**
 * Service responsible for managing navigation state.
 * Uses Angular signals to track the current view.
 */
@Injectable({
  providedIn: 'root',
})
export class NavigationService {
  /** Signal containing the currently active view */
  currentView = signal<View>('chat');

  /**
   * Navigates to a specified view.
   * @param view - The view to navigate to
   */
  navigateTo(view: View): void {
    this.currentView.set(view);
  }
}

