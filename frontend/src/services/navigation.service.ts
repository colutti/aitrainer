
import { Injectable, signal } from '@angular/core';

export type View = 'chat' | 'user-profile' | 'trainer-settings';

@Injectable({
  providedIn: 'root',
})
export class NavigationService {
  currentView = signal<View>('chat');

  navigateTo(view: View): void {
    this.currentView.set(view);
  }
}
