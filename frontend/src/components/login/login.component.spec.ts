import { ComponentFixture, TestBed } from '@angular/core/testing';
import { LoginComponent } from './login.component';
import { AuthService } from '../../services/auth.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

describe('LoginComponent', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let authServiceMock: Partial<AuthService>;

  beforeEach(async () => {
    authServiceMock = {
      login: jest.fn().mockResolvedValue(true)
    };

    await TestBed.configureTestingModule({
      imports: [LoginComponent, FormsModule, CommonModule],
      providers: [
        { provide: AuthService, useValue: authServiceMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
  });

  describe('Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should initialize with empty email', () => {
      expect(component.email()).toBe('');
    });

    it('should initialize with empty password', () => {
      expect(component.password()).toBe('');
    });

    it('should initialize with loading false', () => {
      expect(component.isLoading()).toBe(false);
    });

    it('should initialize with no error', () => {
      expect(component.error()).toBe('');
    });
  });

  describe('Login Success', () => {
    it('should call authService.login with email and password', async () => {
      component.email.set('user@example.com');
      component.password.set('password123');

      await component.login();

      expect(authServiceMock.login).toHaveBeenCalledWith('user@example.com', 'password123');
    });

    it('should set isLoading during login', async () => {
      (authServiceMock.login as jest.Mock).mockImplementation(() => {
        expect(component.isLoading()).toBe(true);
        return Promise.resolve(true);
      });

      component.email.set('user@example.com');
      component.password.set('password123');

      await component.login();

      expect(component.isLoading()).toBe(false);
    });

    it('should clear error on successful login', async () => {
      component.error.set('Previous error');
      component.email.set('user@example.com');
      component.password.set('password123');

      await component.login();

      expect(component.error()).toBe('');
    });

    it('should set isLoading false after successful login', async () => {
      component.email.set('user@example.com');
      component.password.set('password123');

      await component.login();

      expect(component.isLoading()).toBe(false);
    });
  });

  describe('Login Failure', () => {
    it('should show error on invalid credentials', async () => {
      (authServiceMock.login as jest.Mock).mockResolvedValueOnce(false);

      component.email.set('user@example.com');
      component.password.set('wrong_password');

      await component.login();

      expect(component.error()).toBe('Credenciais inválidas. Tente novamente.');
    });

    it('should clear password on failed login', async () => {
      (authServiceMock.login as jest.Mock).mockResolvedValueOnce(false);

      component.email.set('user@example.com');
      component.password.set('wrong_password');

      await component.login();

      expect(component.password()).toBe('');
    });

    it('should keep email on failed login', async () => {
      (authServiceMock.login as jest.Mock).mockResolvedValueOnce(false);

      component.email.set('user@example.com');
      component.password.set('wrong_password');

      await component.login();

      expect(component.email()).toBe('user@example.com');
    });

    it('should set isLoading false on failed login', async () => {
      (authServiceMock.login as jest.Mock).mockResolvedValueOnce(false);

      component.email.set('user@example.com');
      component.password.set('wrong_password');

      await component.login();

      expect(component.isLoading()).toBe(false);
    });
  });

  describe('Login Error', () => {
    it('should show error message on exception', async () => {
      (authServiceMock.login as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      component.email.set('user@example.com');
      component.password.set('password123');

      await component.login();

      expect(component.error()).toBe('Ocorreu um erro. Tente novamente mais tarde.');
    });

    it('should clear password on error', async () => {
      (authServiceMock.login as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      component.email.set('user@example.com');
      component.password.set('password123');

      await component.login();

      expect(component.password()).toBe('');
    });

    it('should set isLoading false on error', async () => {
      (authServiceMock.login as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      component.email.set('user@example.com');
      component.password.set('password123');

      await component.login();

      expect(component.isLoading()).toBe(false);
    });
  });

  describe('Form Input', () => {
    it('should update email signal', () => {
      component.email.set('test@example.com');

      expect(component.email()).toBe('test@example.com');
    });

    it('should update password signal', () => {
      component.password.set('mypassword');

      expect(component.password()).toBe('mypassword');
    });

    it('should accept various email formats', () => {
      const emails = [
        'user@example.com',
        'test.user@example.co.uk',
        'user+tag@example.com'
      ];

      emails.forEach(email => {
        component.email.set(email);
        expect(component.email()).toBe(email);
      });
    });

    it('should accept various password formats', () => {
      const passwords = [
        'simplepassword',
        'P@ssw0rd123!',
        'very long password with spaces 12345'
      ];

      passwords.forEach(password => {
        component.password.set(password);
        expect(component.password()).toBe(password);
      });
    });
  });

  describe('Prevent Duplicate Submission', () => {
    it('should not submit while already loading', async () => {
      component.isLoading.set(true);

      await component.login();

      expect(authServiceMock.login).not.toHaveBeenCalled();
    });

    it('should prevent multiple concurrent logins', async () => {
      (authServiceMock.login as jest.Mock).mockImplementation(() => {
        // After first call, should block second call due to isLoading
        component.email.set('user2@example.com');
        component.password.set('password2');

        // Try to login again
        return component.login().then(() => Promise.resolve(true));
      });

      component.email.set('user@example.com');
      component.password.set('password123');

      await component.login();

      expect(authServiceMock.login).toHaveBeenCalledTimes(1);
    });
  });

  describe('Error State Management', () => {
    it('should clear error before login attempt', async () => {
      component.error.set('Some previous error');
      component.email.set('user@example.com');
      component.password.set('password123');

      (authServiceMock.login as jest.Mock).mockImplementation(() => {
        // Error should be cleared before login is called
        expect(component.error()).toBe('');
        return Promise.resolve(true);
      });

      await component.login();
    });

    it('should maintain error after failed login', async () => {
      (authServiceMock.login as jest.Mock).mockResolvedValueOnce(false);

      component.email.set('user@example.com');
      component.password.set('wrong_password');

      await component.login();

      expect(component.error()).toContain('Credenciais inválidas');
    });

    it('should handle multiple failed login attempts', async () => {
      (authServiceMock.login as jest.Mock).mockResolvedValue(false);

      component.email.set('user@example.com');
      component.password.set('wrong_password');

      // First attempt
      await component.login();
      expect(component.error()).toBe('Credenciais inválidas. Tente novamente.');

      // Second attempt
      component.password.set('another_wrong_password');
      await component.login();
      expect(component.error()).toBe('Credenciais inválidas. Tente novamente.');
    });
  });

  describe('Loading State', () => {
    it('should set isLoading true during login', async () => {
      let loadingState = false;
      (authServiceMock.login as jest.Mock).mockImplementation(() => {
        loadingState = component.isLoading();
        return Promise.resolve(true);
      });

      component.email.set('user@example.com');
      component.password.set('password123');

      await component.login();

      expect(loadingState).toBe(true);
    });

    it('should set isLoading false after login completes', async () => {
      component.email.set('user@example.com');
      component.password.set('password123');

      await component.login();

      expect(component.isLoading()).toBe(false);
    });

    it('should guarantee isLoading false even on error', async () => {
      (authServiceMock.login as jest.Mock).mockRejectedValueOnce(new Error('API Error'));

      component.email.set('user@example.com');
      component.password.set('password123');

      try {
        await component.login();
      } catch {
        // Error expected
      }

      expect(component.isLoading()).toBe(false);
    });
  });

  describe('Credential Handling', () => {
    it('should not clear email after successful login', async () => {
      component.email.set('user@example.com');
      component.password.set('password123');

      await component.login();

      expect(component.email()).toBe('user@example.com');
    });


    it('should clear password after failed login', async () => {
      (authServiceMock.login as jest.Mock).mockResolvedValueOnce(false);

      component.email.set('user@example.com');
      component.password.set('password123');

      await component.login();

      expect(component.password()).toBe('');
    });
  });
});
