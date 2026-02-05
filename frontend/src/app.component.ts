import { Component, ChangeDetectionStrategy, inject, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LoginComponent } from './components/login/login.component';
import { ChatComponent } from './components/chat/chat.component';
import { UserProfileComponent } from './components/user-profile/user-profile.component';
import { TrainerSettingsComponent } from './components/trainer-settings/trainer-settings.component';
import { MemoriesComponent } from './components/memories/memories.component';
import { WorkoutsComponent } from './components/workouts/workouts.component';
import { SidebarComponent } from './components/sidebar/sidebar.component';
import { BottomNavComponent } from './components/bottom-nav/bottom-nav.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { ToastComponent } from './components/toast/toast.component';
import { BodyComponent } from './components/body/body.component';
import { SkeletonComponent } from './components/skeleton/skeleton.component';
import { IntegrationsComponent } from './components/integrations/integrations.component';
import { OnboardingComponent } from './components/onboarding/onboarding.component';
import { AdminDashboardComponent } from './components/admin/admin-dashboard.component';
import { AdminUsersComponent } from './components/admin/admin-users.component';
import { AdminLogsComponent } from './components/admin/admin-logs.component';
import { AdminPromptsComponent } from './components/admin/admin-prompts.component';
import { ConfirmationModalComponent } from './components/shared/confirmation-modal/confirmation-modal.component';
import { AuthService } from './services/auth.service';
import { NavigationService } from './services/navigation.service';
import { TokenExpirationService } from './services/token-expiration.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    LoginComponent,
    ChatComponent,
    UserProfileComponent,
    TrainerSettingsComponent,
    MemoriesComponent,
    WorkoutsComponent,
    BodyComponent,
    SidebarComponent,
    BottomNavComponent,
    DashboardComponent,
    ToastComponent,
    SkeletonComponent,
    IntegrationsComponent,
    OnboardingComponent,
    AdminDashboardComponent,
    AdminUsersComponent,
    AdminLogsComponent,
    AdminPromptsComponent,
    ConfirmationModalComponent
  ],
})

export class AppComponent {
  authService = inject(AuthService);
  navigationService = inject(NavigationService);
  tokenExpirationService = inject(TokenExpirationService);

  isAuthenticated = this.authService.isAuthenticated;
  isCheckingAuth = this.authService.isCheckingAuth;
  currentView = this.navigationService.currentView;

  isMobileMenuOpen = signal(false);
  isOnboarding = signal(false);

  constructor() {
    // Check if URL has onboarding token
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('token')) {
      this.isOnboarding.set(true);
    }

    // Automatically close mobile menu when the view changes
    effect(() => {
      this.currentView(); // Register dependency
      this.isMobileMenuOpen.set(false);
    });

    // Monitor token expiration and automatically logout
    effect(() => {
      const expired = this.tokenExpirationService.tokenExpired();

      if (expired && this.authService.isAuthenticated()) {
        console.log('Token expirado detectado - fazendo logout automático');
        this.authService.logout();
      }
    });
  }

  toggleMobileMenu() {
    this.isMobileMenuOpen.update(v => !v);
  }

  closeMobileMenu() {
    this.isMobileMenuOpen.set(false);
  }
}
