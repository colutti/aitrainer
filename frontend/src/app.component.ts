import { Component, ChangeDetectionStrategy, inject, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LoginComponent } from './components/login/login.component';
import { ChatComponent } from './components/chat/chat.component';
import { UserProfileComponent } from './components/user-profile/user-profile.component';
import { TrainerSettingsComponent } from './components/trainer-settings/trainer-settings.component';
import { MemoriesComponent } from './components/memories/memories.component';
import { WorkoutsComponent } from './components/workouts/workouts.component';
import { SidebarComponent } from './components/sidebar/sidebar.component';
import { AuthService } from './services/auth.service';
import { NavigationService } from './services/navigation.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    LoginComponent,
    ChatComponent,
    UserProfileComponent,
    TrainerSettingsComponent,
    MemoriesComponent,
    WorkoutsComponent,
    SidebarComponent,
  ],
})

export class AppComponent {
  authService = inject(AuthService);
  navigationService = inject(NavigationService);

  isAuthenticated = this.authService.isAuthenticated;
  currentView = this.navigationService.currentView;
  
  isMobileMenuOpen = signal(false);

  constructor() {
    // Automatically close mobile menu when the view changes
    effect(() => {
      this.currentView(); // Register dependency
      this.isMobileMenuOpen.set(false);
    });
  }

  toggleMobileMenu() {
    this.isMobileMenuOpen.update(v => !v);
  }

  closeMobileMenu() {
    this.isMobileMenuOpen.set(false);
  }
}
