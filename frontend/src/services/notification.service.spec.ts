import { TestBed } from '@angular/core/testing';
import { NotificationService } from './notification.service';

describe('NotificationService', () => {
  let service: NotificationService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(NotificationService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should add a toast', () => {
    service.show('Test message');
    expect(service.toasts().length).toBe(1);
    expect(service.toasts()[0].message).toBe('Test message');
  });

  it('should NOT add duplicate simultaneous toasts', () => {
    service.error('Error message');
    service.error('Error message');
    service.error('Error message');
    
    expect(service.toasts().length).toBe(1);
  });

  it('should allow different messages', () => {
    service.success('Success');
    service.error('Error');
    
    expect(service.toasts().length).toBe(2);
  });

  it('should allow same message with different types', () => {
    service.show('Message', 'info');
    service.show('Message', 'error');
    
    expect(service.toasts().length).toBe(2);
  });

  it('should remove toast after duration', (done) => {
    service.show('Temporary', 'info', 100);
    expect(service.toasts().length).toBe(1);
    
    setTimeout(() => {
      expect(service.toasts().length).toBe(0);
      done();
    }, 150);
  });
});
