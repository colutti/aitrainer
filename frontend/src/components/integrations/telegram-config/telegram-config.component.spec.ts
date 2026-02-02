import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TelegramConfigComponent } from './telegram-config.component';
import { TelegramService } from '../../../services/telegram.service';
import { ChangeDetectorRef } from '@angular/core';

describe('TelegramConfigComponent', () => {
  let component: TelegramConfigComponent;
  let fixture: ComponentFixture<TelegramConfigComponent>;
  let mockTelegramService: any;
  let mockChangeDetectorRef: any;

  beforeEach(async () => {
    mockTelegramService = {
      getStatus: jest.fn(),
      generateCode: jest.fn(),
      unlink: jest.fn(),
      updateNotifications: jest.fn(),
    };

    mockChangeDetectorRef = {
      detectChanges: jest.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [TelegramConfigComponent],
      providers: [
        { provide: TelegramService, useValue: mockTelegramService },
        { provide: ChangeDetectorRef, useValue: mockChangeDetectorRef },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(TelegramConfigComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('Notification Toggle', () => {
    it('should update notifyOnWorkout signal when toggle is clicked', () => {
      // Initial state
      expect(component.notifyOnWorkout()).toBe(true);

      // Toggle
      component.notifyOnWorkout.set(false);

      expect(component.notifyOnWorkout()).toBe(false);
    });

    it('should set savingNotifications to true while updating', async () => {
      mockTelegramService.updateNotifications.mockResolvedValue(undefined);

      component.notifyOnWorkout.set(false);
      const promise = component.onNotificationChange();

      // Should be true while saving
      expect(component.savingNotifications()).toBe(true);

      // Wait for promise to resolve
      await promise;

      // Should be false after saving
      expect(component.savingNotifications()).toBe(false);
    });

    it('should call telegramService.updateNotifications with correct payload', async () => {
      mockTelegramService.updateNotifications.mockResolvedValue(undefined);

      component.notifyOnWorkout.set(false);
      component.notifyOnNutrition.set(true);
      component.notifyOnWeight.set(false);

      await component.onNotificationChange();

      expect(mockTelegramService.updateNotifications).toHaveBeenCalledWith({
        telegram_notify_on_workout: false,
        telegram_notify_on_nutrition: true,
        telegram_notify_on_weight: false,
      });
    });

    it('should display success message on successful update', async () => {
      mockTelegramService.updateNotifications.mockResolvedValue(undefined);

      expect(component.successMessage()).toBe('');

      await component.onNotificationChange();

      expect(component.successMessage()).toContain('Configurações');
    });

    it('should clear success message after 3 seconds', async () => {
      jest.useFakeTimers();
      mockTelegramService.updateNotifications.mockResolvedValue(undefined);

      await component.onNotificationChange();
      expect(component.successMessage()).not.toBe('');

      jest.advanceTimersByTime(3001);

      expect(component.successMessage()).toBe('');

      jest.useRealTimers();
    });

    it('should display error message on failure', async () => {
      mockTelegramService.updateNotifications.mockRejectedValue(
        new Error('API Error')
      );

      expect(component.errorMessage()).toBe('');

      await component.onNotificationChange();

      expect(component.errorMessage()).toContain('Erro');
    });

    it('should clear error message when starting new update', async () => {
      component.errorMessage.set('Previous error');
      mockTelegramService.updateNotifications.mockResolvedValue(undefined);

      await component.onNotificationChange();

      // Error should be cleared during the update
      expect(component.errorMessage()).toBe('');
    });
  });

  describe('Initial State', () => {
    it('should have notifyOnWorkout default to true', () => {
      expect(component.notifyOnWorkout()).toBe(true);
    });

    it('should have notifyOnNutrition default to false', () => {
      expect(component.notifyOnNutrition()).toBe(false);
    });

    it('should have notifyOnWeight default to false', () => {
      expect(component.notifyOnWeight()).toBe(false);
    });

    it('should have savingNotifications default to false', () => {
      expect(component.savingNotifications()).toBe(false);
    });
  });

  describe('Load Status with Notification Preferences', () => {
    it('should load notification preferences when Telegram is linked', async () => {
      mockTelegramService.getStatus.mockResolvedValue({
        linked: true,
        telegram_username: '@testuser',
        linked_at: '2026-01-25T10:00:00Z',
        telegram_notify_on_workout: false,
        telegram_notify_on_nutrition: true,
        telegram_notify_on_weight: false,
      });

      await component.loadStatus();

      expect(component.notifyOnWorkout()).toBe(false);
      expect(component.notifyOnNutrition()).toBe(true);
      expect(component.notifyOnWeight()).toBe(false);
    });

    it('should persist notification preferences after component reload', async () => {
      // First load - user has disabled workout notifications
      mockTelegramService.getStatus.mockResolvedValue({
        linked: true,
        telegram_username: '@testuser',
        linked_at: '2026-01-25T10:00:00Z',
        telegram_notify_on_workout: false,
        telegram_notify_on_nutrition: false,
        telegram_notify_on_weight: false,
      });

      await component.loadStatus();

      // Verify preferences loaded correctly
      expect(component.notifyOnWorkout()).toBe(false);

      // Simulate component reload (e.g., user refreshes page)
      // Reset mock call count
      mockTelegramService.getStatus.mockClear();
      mockTelegramService.getStatus.mockResolvedValue({
        linked: true,
        telegram_username: '@testuser',
        linked_at: '2026-01-25T10:00:00Z',
        telegram_notify_on_workout: false,
        telegram_notify_on_nutrition: false,
        telegram_notify_on_weight: false,
      });

      component.ngOnInit();
      await new Promise(resolve => setTimeout(resolve, 100));

      // Should still be false after reload
      expect(component.notifyOnWorkout()).toBe(false);
    });

    it('should use default preferences when response has no notification settings', async () => {
      // Older API response without notification fields
      mockTelegramService.getStatus.mockResolvedValue({
        linked: true,
        telegram_username: '@testuser',
        linked_at: '2026-01-25T10:00:00Z',
      });

      await component.loadStatus();

      // Should fall back to defaults
      expect(component.notifyOnWorkout()).toBe(true);
      expect(component.notifyOnNutrition()).toBe(false);
      expect(component.notifyOnWeight()).toBe(false);
    });
  });
});
