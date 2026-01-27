import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { OnboardingService } from './onboarding.service';
import { environment } from '../environment';

describe('OnboardingService', () => {
  let service: OnboardingService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        OnboardingService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(OnboardingService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('Initialization', () => {
    it('should be created', () => {
      expect(service).toBeTruthy();
    });
  });

  describe('validateToken()', () => {
    it('should validate valid token', async () => {
      const response = {
        valid: true,
        email: 'newuser@example.com'
      };

      const promise = service.validateToken('VALID_TOKEN_123');

      const req = httpMock.expectOne(req =>
        req.url.includes('/onboarding/validate') &&
        req.params.get('token') === 'VALID_TOKEN_123'
      );
      expect(req.request.method).toBe('GET');

      req.flush(response);

      const result = await promise;

      expect(result.valid).toBe(true);
      expect(result.email).toBe('newuser@example.com');
    });

    it('should handle invalid token (404)', async () => {
      const response = {
        valid: false,
        reason: 'Token not found'
      };

      const promise = service.validateToken('INVALID_TOKEN');

      const req = httpMock.expectOne(req =>
        req.url.includes('/onboarding/validate')
      );
      req.flush({ detail: response }, { status: 404, statusText: 'Not Found' });

      const result = await promise;

      expect(result.valid).toBe(false);
      expect(result.reason).toBe('Token not found');
    });

    it('should handle expired token (410)', async () => {
      const response = {
        valid: false,
        reason: 'Token expired'
      };

      const promise = service.validateToken('EXPIRED_TOKEN');

      const req = httpMock.expectOne(req =>
        req.url.includes('/onboarding/validate')
      );
      req.flush({ detail: response }, { status: 410, statusText: 'Gone' });

      const result = await promise;

      expect(result.valid).toBe(false);
      expect(result.reason).toBe('Token expired');
    });

    it('should handle conflict (409)', async () => {
      const response = {
        valid: false,
        reason: 'Email already registered'
      };

      const promise = service.validateToken('CONFLICT_TOKEN');

      const req = httpMock.expectOne(req =>
        req.url.includes('/onboarding/validate')
      );
      req.flush({ detail: response }, { status: 409, statusText: 'Conflict' });

      const result = await promise;

      expect(result.valid).toBe(false);
      expect(result.reason).toBe('Email already registered');
    });

    it('should handle server error (500)', async () => {
      const promise = service.validateToken('TOKEN');

      const req = httpMock.expectOne(req =>
        req.url.includes('/onboarding/validate')
      );
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle network error', async () => {
      const promise = service.validateToken('TOKEN');

      const req = httpMock.expectOne(req =>
        req.url.includes('/onboarding/validate')
      );
      req.error(new ProgressEvent('error'));

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('completeOnboarding()', () => {
    it('should complete onboarding successfully', async () => {
      const onboardingData = {
        token: 'TOKEN_123',
        password: 'securePassword123',
        gender: 'Masculino' as const,
        age: 30,
        weight: 80,
        height: 180,
        goal_type: 'gain' as const,
        weekly_rate: 0.5,
        trainer_type: 'atlas' as const
      };

      const response = {
        token: 'jwt_token_here',
        message: 'Onboarding completed successfully'
      };

      const promise = service.completeOnboarding(onboardingData);

      const req = httpMock.expectOne(req =>
        req.url.includes('/onboarding/complete')
      );
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(onboardingData);

      req.flush(response);

      const result = await promise;

      expect(result.token).toBe('jwt_token_here');
      expect(result.message).toContain('successfully');
    });

    it('should handle validation error (422)', async () => {
      const onboardingData = {
        token: 'TOKEN_123',
        password: 'short', // Too short
        gender: 'Masculino' as const,
        age: -5, // Invalid age
        weight: 0,
        height: 0,
        goal_type: 'gain' as const,
        weekly_rate: 0.5,
        trainer_type: 'atlas' as const
      };

      const promise = service.completeOnboarding(onboardingData);

      const req = httpMock.expectOne(req =>
        req.url.includes('/onboarding/complete')
      );
      req.flush(
        {
          detail: [
            { loc: ['body', 'password'], msg: 'Password must be at least 8 characters' },
            { loc: ['body', 'age'], msg: 'Age must be positive' }
          ]
        },
        { status: 422, statusText: 'Unprocessable Entity' }
      );

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle invalid token (400)', async () => {
      const onboardingData = {
        token: 'INVALID_TOKEN',
        password: 'securePassword123',
        gender: 'Masculino' as const,
        age: 30,
        weight: 80,
        height: 180,
        goal_type: 'gain' as const,
        weekly_rate: 0.5,
        trainer_type: 'atlas' as const
      };

      const promise = service.completeOnboarding(onboardingData);

      const req = httpMock.expectOne(req =>
        req.url.includes('/onboarding/complete')
      );
      req.flush('Invalid token', { status: 400, statusText: 'Bad Request' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle server error (500)', async () => {
      const onboardingData = {
        token: 'TOKEN_123',
        password: 'securePassword123',
        gender: 'Masculino' as const,
        age: 30,
        weight: 80,
        height: 180,
        goal_type: 'gain' as const,
        weekly_rate: 0.5,
        trainer_type: 'atlas' as const
      };

      const promise = service.completeOnboarding(onboardingData);

      const req = httpMock.expectOne(req =>
        req.url.includes('/onboarding/complete')
      );
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle network error', async () => {
      const onboardingData = {
        token: 'TOKEN_123',
        password: 'securePassword123',
        gender: 'Masculino' as const,
        age: 30,
        weight: 80,
        height: 180,
        goal_type: 'gain' as const,
        weekly_rate: 0.5,
        trainer_type: 'atlas' as const
      };

      const promise = service.completeOnboarding(onboardingData);

      const req = httpMock.expectOne(req =>
        req.url.includes('/onboarding/complete')
      );
      req.error(new ProgressEvent('error'));

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('Goal Types', () => {
    it('should support all goal types', async () => {
      const goals = ['lose', 'gain', 'maintain'] as const;

      for (const goal of goals) {
        const data = {
          token: 'TOKEN',
          password: 'password123',
          gender: 'Masculino' as const,
          age: 30,
          weight: 80,
          height: 180,
          goal_type: goal,
          weekly_rate: 0.5,
          trainer_type: 'atlas' as const
        };

        const promise = service.completeOnboarding(data);

        const req = httpMock.expectOne(req =>
          req.url.includes('/onboarding/complete')
        );
        req.flush({ token: 'jwt', message: 'ok' });

        await promise;

        expect(req.request.body.goal_type).toBe(goal);
      }
    });

    it('should support all trainer types', async () => {
      const trainers = ['atlas', 'luna', 'sargento', 'sofia'] as const;

      for (const trainer of trainers) {
        const data = {
          token: 'TOKEN',
          password: 'password123',
          gender: 'Masculino' as const,
          age: 30,
          weight: 80,
          height: 180,
          goal_type: 'gain' as const,
          weekly_rate: 0.5,
          trainer_type: trainer
        };

        const promise = service.completeOnboarding(data);

        const req = httpMock.expectOne(req =>
          req.url.includes('/onboarding/complete')
        );
        req.flush({ token: 'jwt', message: 'ok' });

        await promise;

        expect(req.request.body.trainer_type).toBe(trainer);
      }
    });
  });
});
