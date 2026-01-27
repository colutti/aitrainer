import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TrainerProfileService } from './trainer-profile.service';
import { environment } from '../environment';
import { TrainerFactory } from '../test-utils/factories/trainer.factory';

describe('TrainerProfileService', () => {
  let service: TrainerProfileService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        TrainerProfileService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(TrainerProfileService);
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

  describe('getAvailableTrainers()', () => {
    it('should fetch available trainers', async () => {
      const trainers = TrainerFactory.createAllTrainers();

      const promise = service.getAvailableTrainers();

      const req = httpMock.expectOne(req => req.url.includes('/trainer/available_trainers'));
      expect(req.request.method).toBe('GET');

      req.flush(trainers);

      const result = await promise;

      expect(result).toEqual(trainers);
      expect(result.length).toBe(5);
      expect(result[0].name).toBe('Atlas');
    });

    it('should handle error fetching trainers', async () => {
      const promise = service.getAvailableTrainers();

      const req = httpMock.expectOne(req => req.url.includes('/trainer/available_trainers'));
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle 401 unauthorized', async () => {
      const promise = service.getAvailableTrainers();

      const req = httpMock.expectOne(req => req.url.includes('/trainer/available_trainers'));
      req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle network error', async () => {
      const promise = service.getAvailableTrainers();

      const req = httpMock.expectOne(req => req.url.includes('/trainer/available_trainers'));
      req.error(new ProgressEvent('error'));

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('fetchProfile()', () => {
    it('should fetch trainer profile successfully', async () => {
      const profile = TrainerFactory.create('luna');

      const promise = service.fetchProfile();

      const req = httpMock.expectOne(req => req.url.includes('/trainer/trainer_profile'));
      expect(req.request.method).toBe('GET');

      req.flush(profile);

      const result = await promise;

      expect(result).toEqual(profile);
      expect(result.trainer_type).toBe('luna');
    });

    it('should return default profile on error', async () => {
      const promise = service.fetchProfile();

      const req = httpMock.expectOne(req => req.url.includes('/trainer/trainer_profile'));
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });

      const result = await promise;

      expect(result.trainer_type).toBe('atlas'); // Default
    });

    it('should return default profile on 404', async () => {
      const promise = service.fetchProfile();

      const req = httpMock.expectOne(req => req.url.includes('/trainer/trainer_profile'));
      req.flush('Not Found', { status: 404, statusText: 'Not Found' });

      const result = await promise;

      expect(result.trainer_type).toBe('atlas');
    });

    it('should return default profile on 401', async () => {
      const promise = service.fetchProfile();

      const req = httpMock.expectOne(req => req.url.includes('/trainer/trainer_profile'));
      req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

      const result = await promise;

      expect(result.trainer_type).toBe('atlas');
    });

    it('should return default profile on network error', async () => {
      const promise = service.fetchProfile();

      const req = httpMock.expectOne(req => req.url.includes('/trainer/trainer_profile'));
      req.error(new ProgressEvent('error'));

      const result = await promise;

      expect(result.trainer_type).toBe('atlas');
    });

    it('should return default profile if response has no trainer_type', async () => {
      const invalidProfile = { trainer_type: null };

      const promise = service.fetchProfile();

      const req = httpMock.expectOne(req => req.url.includes('/trainer/trainer_profile'));
      req.flush(invalidProfile);

      const result = await promise;

      expect(result.trainer_type).toBe('atlas');
    });

    it('should return default profile if response is empty object', async () => {
      const promise = service.fetchProfile();

      const req = httpMock.expectOne(req => req.url.includes('/trainer/trainer_profile'));
      req.flush({});

      const result = await promise;

      expect(result.trainer_type).toBe('atlas');
    });

    it('should validate trainer_type property', async () => {
      const validProfile = TrainerFactory.create('sofia');

      const promise = service.fetchProfile();

      const req = httpMock.expectOne(req => req.url.includes('/trainer/trainer_profile'));
      req.flush(validProfile);

      const result = await promise;

      expect(result.trainer_type).toBe('sofia');
    });
  });

  describe('updateProfile()', () => {
    it('should update trainer profile successfully', async () => {
      const newProfile = TrainerFactory.create('gymbro');

      const promise = service.updateProfile(newProfile);

      const req = httpMock.expectOne(req => req.url.includes('/trainer/update_trainer_profile'));
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual(newProfile);

      req.flush(newProfile);

      const result = await promise;

      expect(result).toEqual(newProfile);
      expect(result.trainer_type).toBe('gymbro');
    });

    it('should handle error updating profile', async () => {
      const profile = TrainerFactory.create('luna');

      const promise = service.updateProfile(profile);

      const req = httpMock.expectOne(req => req.url.includes('/trainer/update_trainer_profile'));
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle 401 unauthorized on update', async () => {
      const profile = TrainerFactory.create('luna');

      const promise = service.updateProfile(profile);

      const req = httpMock.expectOne(req => req.url.includes('/trainer/update_trainer_profile'));
      req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle validation error on update', async () => {
      const profile = TrainerFactory.create('invalid');

      const promise = service.updateProfile(profile);

      const req = httpMock.expectOne(req => req.url.includes('/trainer/update_trainer_profile'));
      req.flush(
        { detail: [{ loc: ['body', 'trainer_type'], msg: 'Invalid trainer type' }] },
        { status: 422, statusText: 'Unprocessable Entity' }
      );

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle network error on update', async () => {
      const profile = TrainerFactory.create('luna');

      const promise = service.updateProfile(profile);

      const req = httpMock.expectOne(req => req.url.includes('/trainer/update_trainer_profile'));
      req.error(new ProgressEvent('error'));

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('Trainer Types', () => {
    it('should support all trainer types in fetch', async () => {
      const types = ['atlas', 'luna', 'sofia', 'sargento', 'gymbro'];

      for (const type of types) {
        const promise = service.fetchProfile();

        const req = httpMock.expectOne(req => req.url.includes('/trainer/trainer_profile'));
        req.flush(TrainerFactory.create(type));

        const result = await promise;
        expect(result.trainer_type).toBe(type);
      }
    });

    it('should update to any valid trainer type', async () => {
      const types = ['atlas', 'luna', 'sofia', 'sargento', 'gymbro'];

      for (const type of types) {
        const profile = TrainerFactory.create(type);
        const promise = service.updateProfile(profile);

        const req = httpMock.expectOne(req => req.url.includes('/trainer/update_trainer_profile'));
        req.flush(profile);

        const result = await promise;
        expect(result.trainer_type).toBe(type);
      }
    });
  });
});
