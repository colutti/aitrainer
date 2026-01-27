import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient, HttpErrorResponse } from '@angular/common/http';
import { UserProfileService } from './user-profile.service';
import { environment } from '../environment';
import { UserProfileFactory } from '../test-utils/factories/user-profile.factory';

describe('UserProfileService', () => {
  let service: UserProfileService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        UserProfileService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(UserProfileService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('Initialization', () => {
    it('should be created', () => {
      expect(service).toBeTruthy();
    });

    it('should initialize with null profile', () => {
      expect(service.userProfile()).toBeNull();
    });
  });

  describe('getProfile()', () => {
    it('should fetch user profile successfully', async () => {
      const mockProfile = UserProfileFactory.create();

      const promise = service.getProfile();

      const req = httpMock.expectOne(`${environment.apiUrl}/user/profile`);
      expect(req.request.method).toBe('GET');

      req.flush(mockProfile);

      const result = await promise;

      expect(result).toEqual(mockProfile);
      expect(service.userProfile()).toEqual(mockProfile);
    });

    it('should handle multiple getProfile calls independently', async () => {
      const profile1 = UserProfileFactory.createMale();
      const profile2 = UserProfileFactory.createFemale();

      // First call
      let promise = service.getProfile();
      let req = httpMock.expectOne(`${environment.apiUrl}/user/profile`);
      req.flush(profile1);
      let result = await promise;
      expect(result).toEqual(profile1);

      // Second call
      promise = service.getProfile();
      req = httpMock.expectOne(`${environment.apiUrl}/user/profile`);
      req.flush(profile2);
      result = await promise;
      expect(result).toEqual(profile2);
      expect(service.userProfile()).toEqual(profile2);
    });

    it('should handle 401 unauthorized', async () => {
      const promise = service.getProfile();

      const req = httpMock.expectOne(`${environment.apiUrl}/user/profile`);
      req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

      const result = await promise;

      expect(result).toBeNull();
      expect(service.userProfile()).toBeNull();
    });

    it('should handle 404 not found', async () => {
      const promise = service.getProfile();

      const req = httpMock.expectOne(`${environment.apiUrl}/user/profile`);
      req.flush('Not Found', { status: 404, statusText: 'Not Found' });

      const result = await promise;

      expect(result).toBeNull();
    });

    it('should handle 500 server error', async () => {
      const promise = service.getProfile();

      const req = httpMock.expectOne(`${environment.apiUrl}/user/profile`);
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });

      const result = await promise;

      expect(result).toBeNull();
    });

    it('should handle network error', async () => {
      const promise = service.getProfile();

      const req = httpMock.expectOne(`${environment.apiUrl}/user/profile`);
      req.error(new ProgressEvent('error'));

      const result = await promise;

      expect(result).toBeNull();
    });
  });

  describe('updateProfile()', () => {
    it('should update profile successfully', async () => {
      const currentProfile = UserProfileFactory.create();
      const updateData = { age: 35, weight: 85 };

      // Set initial profile
      service.userProfile.set(currentProfile);

      const promise = service.updateProfile(updateData as any);

      const req = httpMock.expectOne(`${environment.apiUrl}/user/update_profile`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(updateData);

      req.flush({ success: true });

      await promise;

      const updated = service.userProfile();
      expect(updated?.age).toBe(35);
      expect(updated?.weight).toBe(85);
    });

    it('should merge updated fields with current profile', async () => {
      const currentProfile = UserProfileFactory.create({
        age: 30,
        weight: 80,
        height: 180
      });

      service.userProfile.set(currentProfile);

      const updateData = { age: 35 };

      const promise = service.updateProfile(updateData as any);

      const req = httpMock.expectOne(`${environment.apiUrl}/user/update_profile`);
      req.flush({ success: true });

      await promise;

      const updated = service.userProfile();
      expect(updated?.age).toBe(35);
      expect(updated?.weight).toBe(80); // Should keep original
      expect(updated?.height).toBe(180); // Should keep original
    });

    it('should create profile if none exists', async () => {
      service.userProfile.set(null);

      const updateData = {
        email: 'new@example.com',
        age: 25,
        weight: 75,
        height: 175,
        gender: 'Masculino' as const,
        goal: 'Ganhar massa' as const
      };

      const promise = service.updateProfile(updateData as any);

      const req = httpMock.expectOne(`${environment.apiUrl}/user/update_profile`);
      req.flush({ success: true });

      await promise;

      const profile = service.userProfile();
      expect(profile).toBeTruthy();
      expect(profile?.email).toBe('new@example.com');
    });

    it('should throw validation error on 422', async () => {
      const updateData = { email: 'invalid-email' };

      const promise = service.updateProfile(updateData as any);

      const req = httpMock.expectOne(`${environment.apiUrl}/user/update_profile`);
      req.flush(
        { detail: [{ loc: ['body', 'email'], msg: 'Invalid email format' }] },
        { status: 422, statusText: 'Unprocessable Entity' }
      );

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error: any) {
        expect(Array.isArray(error)).toBe(true);
        expect(error[0].loc).toContain('email');
        expect(error[0].msg).toContain('Invalid email');
      }
    });

    it('should throw generic error on other failures', async () => {
      const updateData = { age: 30 };

      const promise = service.updateProfile(updateData as any);

      const req = httpMock.expectOne(`${environment.apiUrl}/user/update_profile`);
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error: any) {
        expect(error.message).toBe('An unexpected error occurred.');
      }
    });

    it('should handle 401 unauthorized', async () => {
      const updateData = { age: 30 };

      const promise = service.updateProfile(updateData as any);

      const req = httpMock.expectOne(`${environment.apiUrl}/user/update_profile`);
      req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error: any) {
        expect(error.message).toBe('An unexpected error occurred.');
      }
    });

    it('should handle multiple validation errors', async () => {
      const updateData = { email: 'invalid', age: -5 };

      const promise = service.updateProfile(updateData as any);

      const req = httpMock.expectOne(`${environment.apiUrl}/user/update_profile`);
      req.flush(
        {
          detail: [
            { loc: ['body', 'email'], msg: 'Invalid email format' },
            { loc: ['body', 'age'], msg: 'Age must be positive' }
          ]
        },
        { status: 422, statusText: 'Unprocessable Entity' }
      );

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error: any) {
        expect(error.length).toBe(2);
        expect(error[0].loc).toContain('email');
        expect(error[1].loc).toContain('age');
      }
    });

    it('should handle network error', async () => {
      const updateData = { age: 30 };

      const promise = service.updateProfile(updateData as any);

      const req = httpMock.expectOne(`${environment.apiUrl}/user/update_profile`);
      req.error(new ProgressEvent('error'));

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error: any) {
        expect(error.message).toBe('An unexpected error occurred.');
      }
    });
  });

  describe('Profile Updates', () => {
    it('should update individual fields', async () => {
      const initial = UserProfileFactory.create();
      service.userProfile.set(initial);

      // Update age only
      let promise = service.updateProfile({ age: 35 } as any);
      let req = httpMock.expectOne(`${environment.apiUrl}/user/update_profile`);
      req.flush({ success: true });
      await promise;

      expect(service.userProfile()?.age).toBe(35);

      // Update weight only
      promise = service.updateProfile({ weight: 85 } as any);
      req = httpMock.expectOne(`${environment.apiUrl}/user/update_profile`);
      req.flush({ success: true });
      await promise;

      expect(service.userProfile()?.weight).toBe(85);
      expect(service.userProfile()?.age).toBe(35); // Should keep previous
    });

    it('should handle empty update', async () => {
      const initial = UserProfileFactory.create();
      service.userProfile.set(initial);

      const promise = service.updateProfile({} as any);

      const req = httpMock.expectOne(`${environment.apiUrl}/user/update_profile`);
      req.flush({ success: true });

      await promise;

      // Profile should remain unchanged
      expect(service.userProfile()).toEqual(initial);
    });
  });
});
