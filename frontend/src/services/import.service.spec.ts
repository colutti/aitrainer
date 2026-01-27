import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ImportService } from './import.service';
import { environment } from '../environment';

describe('ImportService', () => {
  let service: ImportService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ImportService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(ImportService);
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

  describe('uploadMyFitnessPalCSV()', () => {
    it('should upload CSV file successfully', (done) => {
      const csvContent = 'Date,Meal Type,Food,Calories,Protein,Carbs,Fat\n2026-01-27,Breakfast,Eggs,150,12,0,5';
      const file = new File([csvContent], 'nutrition.csv', { type: 'text/csv' });

      const observable = service.uploadMyFitnessPalCSV(file);

      const subscription = observable.subscribe(result => {
        expect(result.success).toBe(true);
        expect(result.imported).toBe(1);
        subscription.unsubscribe();
        done();
      });

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      expect(req.request.method).toBe('POST');
      expect(req.request.body instanceof FormData).toBe(true);

      // Verify FormData contains file
      const formData = req.request.body as FormData;
      expect(formData.has('file')).toBe(true);

      req.flush({
        success: true,
        imported: 1,
        skipped: 0,
        errors: []
      });
    });

    it('should handle file with multiple entries', (done) => {
      const csvContent = `Date,Meal Type,Food,Calories,Protein,Carbs,Fat
2026-01-25,Breakfast,Eggs,150,12,0,5
2026-01-25,Lunch,Chicken,400,50,0,15
2026-01-25,Dinner,Rice,300,10,60,5
2026-01-26,Breakfast,Oats,250,10,45,5
2026-01-26,Lunch,Salmon,450,40,0,20`;

      const file = new File([csvContent], 'nutrition_multi.csv', { type: 'text/csv' });

      const observable = service.uploadMyFitnessPalCSV(file);

      const subscription = observable.subscribe(result => {
        expect(result.success).toBe(true);
        expect(result.imported).toBe(5);
        subscription.unsubscribe();
        done();
      });

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      req.flush({
        success: true,
        imported: 5,
        skipped: 0,
        errors: []
      });
    });

    it('should handle file with some skipped entries', (done) => {
      const csvContent = 'Date,Meal Type,Food,Calories,Protein,Carbs,Fat\n2026-01-27,Breakfast,Eggs,150,12,0,5';
      const file = new File([csvContent], 'nutrition.csv', { type: 'text/csv' });

      const observable = service.uploadMyFitnessPalCSV(file);

      const subscription = observable.subscribe(result => {
        expect(result.success).toBe(true);
        expect(result.imported).toBe(8);
        expect(result.skipped).toBe(2);
        subscription.unsubscribe();
        done();
      });

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      req.flush({
        success: true,
        imported: 8,
        skipped: 2,
        errors: []
      });
    });

    it('should handle file with some errors', (done) => {
      const csvContent = 'Date,Meal Type,Food,Calories,Protein,Carbs,Fat\n2026-01-27,Breakfast,Eggs,invalid,12,0,5';
      const file = new File([csvContent], 'nutrition.csv', { type: 'text/csv' });

      const observable = service.uploadMyFitnessPalCSV(file);

      const subscription = observable.subscribe(result => {
        expect(result.success).toBe(true);
        expect(result.imported).toBe(5);
        expect(result.errors.length).toBe(1);
        subscription.unsubscribe();
        done();
      });

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      req.flush({
        success: true,
        imported: 5,
        skipped: 0,
        errors: [
          { row: 2, error: 'Invalid calories value' }
        ]
      });
    });

    it('should handle validation error (422)', (done) => {
      const file = new File(['invalid'], 'invalid.txt', { type: 'text/plain' });

      const observable = service.uploadMyFitnessPalCSV(file);

      const subscription = observable.subscribe(
        () => {
          fail('Should have thrown error');
        },
        error => {
          expect(error.status).toBe(422);
          subscription.unsubscribe();
          done();
        }
      );

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      req.flush(
        { detail: 'Invalid CSV format' },
        { status: 422, statusText: 'Unprocessable Entity' }
      );
    });

    it('should handle file too large error', (done) => {
      const file = new File(['content'], 'large.csv', { type: 'text/csv' });

      const observable = service.uploadMyFitnessPalCSV(file);

      const subscription = observable.subscribe(
        () => {
          fail('Should have thrown error');
        },
        error => {
          expect(error.status).toBe(413);
          subscription.unsubscribe();
          done();
        }
      );

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      req.flush(
        { detail: 'File too large' },
        { status: 413, statusText: 'Payload Too Large' }
      );
    });

    it('should handle server error (500)', (done) => {
      const file = new File(['content'], 'nutrition.csv', { type: 'text/csv' });

      const observable = service.uploadMyFitnessPalCSV(file);

      const subscription = observable.subscribe(
        () => {
          fail('Should have thrown error');
        },
        error => {
          expect(error.status).toBe(500);
          subscription.unsubscribe();
          done();
        }
      );

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      req.flush(
        { detail: 'Server error during import' },
        { status: 500, statusText: 'Internal Server Error' }
      );
    });

    it('should handle unauthorized error (401)', (done) => {
      const file = new File(['content'], 'nutrition.csv', { type: 'text/csv' });

      const observable = service.uploadMyFitnessPalCSV(file);

      const subscription = observable.subscribe(
        () => {
          fail('Should have thrown error');
        },
        error => {
          expect(error.status).toBe(401);
          subscription.unsubscribe();
          done();
        }
      );

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      req.flush(
        { detail: 'Unauthorized' },
        { status: 401, statusText: 'Unauthorized' }
      );
    });

    it('should send FormData with correct content-type', (done) => {
      const file = new File(['content'], 'nutrition.csv', { type: 'text/csv' });

      const observable = service.uploadMyFitnessPalCSV(file);

      const subscription = observable.subscribe(
        result => {
          expect(result.success).toBe(true);
          subscription.unsubscribe();
          done();
        },
        error => {
          fail('Should not error: ' + error);
        }
      );

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      // FormData requests should not set Content-Type (browser sets it with boundary)
      expect(req.request.headers.has('Content-Type')).toBeFalsy();

      // Verify FormData is used
      expect(req.request.body instanceof FormData).toBe(true);

      req.flush({ success: true, imported: 1, skipped: 0, errors: [] });
    });

    it('should handle empty response', (done) => {
      const file = new File(['content'], 'nutrition.csv', { type: 'text/csv' });

      const observable = service.uploadMyFitnessPalCSV(file);

      const subscription = observable.subscribe(
        result => {
          expect(result).toEqual({});
          subscription.unsubscribe();
          done();
        }
      );

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      req.flush({});
    });

    it('should return observable that can be subscribed multiple times', (done) => {
      const file = new File(['content'], 'nutrition.csv', { type: 'text/csv' });

      const observable = service.uploadMyFitnessPalCSV(file);

      let completedCount = 0;

      // First subscription
      observable.subscribe(
        result => {
          expect(result.success).toBe(true);
          completedCount++;
        }
      );

      // Second subscription
      observable.subscribe(
        result => {
          expect(result.success).toBe(true);
          completedCount++;

          if (completedCount === 2) {
            done();
          }
        }
      );

      // Handle both requests
      const reqs = httpMock.match(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );
      expect(reqs.length).toBe(2);

      reqs.forEach(req => {
        req.flush({ success: true, imported: 1, skipped: 0, errors: [] });
      });
    });
  });

  describe('File Types', () => {
    it('should accept various CSV MIME types', (done) => {
      const mimeTypes = ['text/csv', 'text/plain', 'application/csv'];

      let completed = 0;

      mimeTypes.forEach((mimeType, index) => {
        const file = new File(['content'], `file_${index}.csv`, { type: mimeType });

        const observable = service.uploadMyFitnessPalCSV(file);

        observable.subscribe(result => {
          expect(result.success).toBe(true);
          completed++;

          if (completed === mimeTypes.length) {
            done();
          }
        });

        const req = httpMock.expectOne(req =>
          req.url.includes('/nutrition/import/myfitnesspal')
        );

        req.flush({ success: true, imported: 1, skipped: 0, errors: [] });
      });
    });

    it('should preserve original filename in FormData', (done) => {
      const filename = 'myfitnesspal_export_2026-01-27.csv';
      const file = new File(['content'], filename, { type: 'text/csv' });

      const observable = service.uploadMyFitnessPalCSV(file);

      const subscription = observable.subscribe(result => {
        expect(result.success).toBe(true);
        subscription.unsubscribe();
        done();
      });

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      const formData = req.request.body as FormData;
      const uploadedFile = formData.get('file') as File;

      expect(uploadedFile.name).toBe(filename);

      req.flush({ success: true, imported: 1, skipped: 0, errors: [] });
    });
  });
});
