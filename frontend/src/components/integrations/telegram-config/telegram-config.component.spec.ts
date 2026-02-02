import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TelegramConfigComponent } from './telegram-config.component';
import { TelegramService } from '../../../services/telegram.service';
import { ChangeDetectorRef } from '@angular/core';

describe('TelegramConfigComponent', () => {
  let component: TelegramConfigComponent;
  let fixture: ComponentFixture<TelegramConfigComponent>;
  let mockTelegramService: jasmine.SpyObj<TelegramService>;
  let mockChangeDetectorRef: jasmine.SpyObj<ChangeDetectorRef>;

  beforeEach(async () => {
    mockTelegramService = jasmine.createSpyObj('TelegramService', [
      'getStatus',
      'generateCode',
      'unlink',
      'updateNotifications',
    ]);

    mockChangeDetectorRef = jasmine.createSpyObj('ChangeDetectorRef', [
      'detectChanges',
    ]);

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
      mockTelegramService.updateNotifications.and.returnValue(
        Promise.resolve()
      );

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
      mockTelegramService.updateNotifications.and.returnValue(
        Promise.resolve()
      );

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
      mockTelegramService.updateNotifications.and.returnValue(
        Promise.resolve()
      );

      expect(component.successMessage()).toBe('');

      await component.onNotificationChange();

      expect(component.successMessage()).toContain('Configurações');
    });

    it('should clear success message after 3 seconds', async () => {
      mockTelegramService.updateNotifications.and.returnValue(
        Promise.resolve()
      );

      jasmine.clock().install();

      await component.onNotificationChange();
      expect(component.successMessage()).not.toBe('');

      jasmine.clock().tick(3001);

      expect(component.successMessage()).toBe('');

      jasmine.clock().uninstall();
    });

    it('should display error message on failure', async () => {
      mockTelegramService.updateNotifications.and.returnValue(
        Promise.reject(new Error('API Error'))
      );

      expect(component.errorMessage()).toBe('');

      await component.onNotificationChange();

      expect(component.errorMessage()).toContain('Erro');
    });

    it('should clear error message when starting new update', async () => {
      component.errorMessage.set('Previous error');
      mockTelegramService.updateNotifications.and.returnValue(
        Promise.resolve()
      );

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
});
