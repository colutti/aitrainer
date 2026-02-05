import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService } from '../../services/auth.service';
import { NavigationService, View } from '../../services/navigation.service';

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, LucideAngularModule]
})
export class SidebarComponent {
  authService = inject(AuthService);
  navigationService = inject(NavigationService);

  currentView = this.navigationService.currentView;

  navigateTo(view: View): void {
    this.navigationService.navigateTo(view);
  }

  async logout(): Promise<void> {
    await this.authService.logout();
  }
}
