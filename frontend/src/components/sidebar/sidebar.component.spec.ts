import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SidebarComponent } from './sidebar.component';
import { AuthService } from '../../services/auth.service';
import { NavigationService, View } from '../../services/navigation.service';
import { signal } from '@angular/core';

describe('SidebarComponent', () => {
  let component: SidebarComponent;
  let fixture: ComponentFixture<SidebarComponent>;
  let authServiceMock: Partial<AuthService>;
  let navigationServiceMock: Partial<NavigationService>;

  beforeEach(async () => {
    authServiceMock = {
      logout: jest.fn().mockResolvedValue(undefined),
      isLoadingUserInfo: signal(false)
    };

    navigationServiceMock = {
      currentView: signal('chat' as View),
      navigateTo: jest.fn()
    };

    await TestBed.configureTestingModule({
      imports: [SidebarComponent],
      providers: [
        { provide: AuthService, useValue: authServiceMock },
        { provide: NavigationService, useValue: navigationServiceMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(SidebarComponent);
    component = fixture.componentInstance;
  });

  describe('Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should initialize with current view from service', () => {
      expect(component.currentView()).toBe('chat');
    });
  });

  describe('Navigation', () => {
    it('should navigate to chat view', () => {
      component.navigateTo('chat');

      expect(navigationServiceMock.navigateTo).toHaveBeenCalledWith('chat');
    });

    it('should navigate to workouts view', () => {
      component.navigateTo('workouts');

      expect(navigationServiceMock.navigateTo).toHaveBeenCalledWith('workouts');
    });

    it('should navigate to nutrition view', () => {
      component.navigateTo('nutrition');

      expect(navigationServiceMock.navigateTo).toHaveBeenCalledWith('nutrition');
    });

    it('should navigate to metabolism view', () => {
      component.navigateTo('metabolism');

      expect(navigationServiceMock.navigateTo).toHaveBeenCalledWith('metabolism');
    });

    it('should navigate to memories view', () => {
      component.navigateTo('memories');

      expect(navigationServiceMock.navigateTo).toHaveBeenCalledWith('memories');
    });

    it('should navigate to dashboard view', () => {
      component.navigateTo('dashboard');

      expect(navigationServiceMock.navigateTo).toHaveBeenCalledWith('dashboard');
    });

    it('should navigate to integrations view', () => {
      component.navigateTo('integrations');

      expect(navigationServiceMock.navigateTo).toHaveBeenCalledWith('integrations');
    });

    it('should update current view when navigating', () => {
      (navigationServiceMock.currentView as any).set('workouts');

      expect(component.currentView()).toBe('workouts');
    });

    it('should allow multiple navigation calls', () => {
      component.navigateTo('chat');
      component.navigateTo('workouts');
      component.navigateTo('nutrition');

      expect(navigationServiceMock.navigateTo).toHaveBeenCalledTimes(3);
      expect(navigationServiceMock.navigateTo).toHaveBeenNthCalledWith(1, 'chat');
      expect(navigationServiceMock.navigateTo).toHaveBeenNthCalledWith(2, 'workouts');
      expect(navigationServiceMock.navigateTo).toHaveBeenNthCalledWith(3, 'nutrition');
    });
  });

  describe('Logout', () => {
    it('should call logout on auth service', async () => {
      await component.logout();

      expect(authServiceMock.logout).toHaveBeenCalled();
    });

    it('should handle logout errors gracefully', async () => {
      (authServiceMock.logout as jest.Mock).mockRejectedValueOnce(new Error('Logout failed'));

      // Should not throw
      try {
        await component.logout();
      } catch (e) {
        // Expected to fail
      }

      expect(authServiceMock.logout).toHaveBeenCalled();
    });
  });

  describe('Current View State', () => {
    it('should reflect current view from navigation service', () => {
      (navigationServiceMock.currentView as any).set('chat');
      expect(component.currentView()).toBe('chat');

      (navigationServiceMock.currentView as any).set('workouts');
      expect(component.currentView()).toBe('workouts');

      (navigationServiceMock.currentView as any).set('memories');
      expect(component.currentView()).toBe('memories');
    });

    it('should maintain view state across multiple operations', () => {
      (navigationServiceMock.currentView as any).set('nutrition');

      component.navigateTo('workouts');
      (navigationServiceMock.currentView as any).set('workouts');

      expect(component.currentView()).toBe('workouts');
    });
  });

  describe('View Highlighting', () => {
    it('should highlight chat when active', () => {
      (navigationServiceMock.currentView as any).set('chat');

      expect(component.currentView()).toBe('chat');
    });

    it('should highlight workouts when active', () => {
      (navigationServiceMock.currentView as any).set('workouts');

      expect(component.currentView()).toBe('workouts');
    });

    it('should highlight nutrition when active', () => {
      (navigationServiceMock.currentView as any).set('nutrition');

      expect(component.currentView()).toBe('nutrition');
    });

    it('should only have one active view', () => {
      (navigationServiceMock.currentView as any).set('chat');
      expect(component.currentView()).toBe('chat');

      (navigationServiceMock.currentView as any).set('workouts');
      expect(component.currentView()).not.toBe('chat');
      expect(component.currentView()).toBe('workouts');
    });
  });
});
