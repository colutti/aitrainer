import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ToastComponent } from './toast.component';
import { NotificationService } from '../../services/notification.service';
import { signal } from '@angular/core';

describe('ToastComponent', () => {
  let component: ToastComponent;
  let fixture: ComponentFixture<ToastComponent>;
  let notificationServiceMock: Partial<NotificationService>;

  beforeEach(async () => {
    notificationServiceMock = {
      toasts: signal([]),
      remove: jest.fn()
    };

    await TestBed.configureTestingModule({
      imports: [ToastComponent],
      providers: [
        { provide: NotificationService, useValue: notificationServiceMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ToastComponent);
    component = fixture.componentInstance;
  });

  describe('Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should initialize with empty toasts', () => {
      expect(component.toasts()).toEqual([]);
    });
  });

  describe('Display Toasts', () => {
    it('should display toasts from service', () => {
      const mockToasts = [
        { id: 1, message: 'Success message', type: 'success' },
        { id: 2, message: 'Error message', type: 'error' }
      ];

      (notificationServiceMock.toasts as any).set(mockToasts);

      expect(component.toasts().length).toBe(2);
      expect(component.toasts()[0].message).toBe('Success message');
      expect(component.toasts()[1].message).toBe('Error message');
    });

    it('should show empty when no toasts', () => {
      (notificationServiceMock.toasts as any).set([]);

      expect(component.toasts()).toEqual([]);
    });

    it('should display multiple toasts simultaneously', () => {
      const mockToasts = [
        { id: 1, message: 'Message 1', type: 'success' },
        { id: 2, message: 'Message 2', type: 'info' },
        { id: 3, message: 'Message 3', type: 'error' }
      ];

      (notificationServiceMock.toasts as any).set(mockToasts);

      expect(component.toasts().length).toBe(3);
    });
  });

  describe('Remove Toast', () => {
    it('should remove toast by id', () => {
      component.remove(1);

      expect(notificationServiceMock.remove).toHaveBeenCalledWith(1);
    });

    it('should call service remove method', () => {
      const id = 42;

      component.remove(id);

      expect(notificationServiceMock.remove).toHaveBeenCalledWith(42);
    });

    it('should allow removing multiple toasts', () => {
      component.remove(1);
      component.remove(2);
      component.remove(3);

      expect(notificationServiceMock.remove).toHaveBeenCalledTimes(3);
      expect(notificationServiceMock.remove).toHaveBeenNthCalledWith(1, 1);
      expect(notificationServiceMock.remove).toHaveBeenNthCalledWith(2, 2);
      expect(notificationServiceMock.remove).toHaveBeenNthCalledWith(3, 3);
    });
  });

  describe('Toast Types', () => {
    it('should handle success type toasts', () => {
      const mockToasts = [
        { id: 1, message: 'Success!', type: 'success' }
      ];

      (notificationServiceMock.toasts as any).set(mockToasts);

      expect(component.toasts()[0].type).toBe('success');
    });

    it('should handle error type toasts', () => {
      const mockToasts = [
        { id: 1, message: 'Error!', type: 'error' }
      ];

      (notificationServiceMock.toasts as any).set(mockToasts);

      expect(component.toasts()[0].type).toBe('error');
    });

    it('should handle info type toasts', () => {
      const mockToasts = [
        { id: 1, message: 'Info', type: 'info' }
      ];

      (notificationServiceMock.toasts as any).set(mockToasts);

      expect(component.toasts()[0].type).toBe('info');
    });
  });
});
