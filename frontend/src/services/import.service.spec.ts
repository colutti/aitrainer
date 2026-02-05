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
    it('should upload CSV file successfully', async () => {
      const csvContent = 'Date,Meal Type,Food,Calories,Protein,Carbs,Fat\n2026-01-27,Breakfast,Eggs,150,12,0,5';
      const file = new File([csvContent], 'nutrition.csv', { type: 'text/csv' });

      const promise = service.uploadMyFitnessPalCSV(file);

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

      const result = await promise;
      expect(result.success).toBe(true);
      expect(result.imported).toBe(1);
    });

    it('should handle file with multiple entries', async () => {
      const csvContent = `Date,Meal Type,Food,Calories,Protein,Carbs,Fat
2026-01-25,Breakfast,Eggs,150,12,0,5
2026-01-25,Lunch,Chicken,400,50,0,15
2026-01-25,Dinner,Rice,300,10,60,5
2026-01-26,Breakfast,Oats,250,10,45,5
2026-01-26,Lunch,Salmon,450,40,0,20`;

      const file = new File([csvContent], 'nutrition_multi.csv', { type: 'text/csv' });

      const promise = service.uploadMyFitnessPalCSV(file);

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      req.flush({
        success: true,
        imported: 5,
        skipped: 0,
        errors: []
      });

      const result = await promise;
      expect(result.success).toBe(true);
      expect(result.imported).toBe(5);
    });

    it('should handle file with some skipped entries', async () => {
      const csvContent = 'Date,Meal Type,Food,Calories,Protein,Carbs,Fat\n2026-01-27,Breakfast,Eggs,150,12,0,5';
      const file = new File([csvContent], 'nutrition.csv', { type: 'text/csv' });

      const promise = service.uploadMyFitnessPalCSV(file);

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      req.flush({
        success: true,
        imported: 8,
        skipped: 2,
        errors: []
      });

      const result = await promise;
      expect(result.success).toBe(true);
      expect(result.imported).toBe(8);
      expect(result.skipped).toBe(2);
    });

    it('should handle file with some errors', async () => {
      const csvContent = 'Date,Meal Type,Food,Calories,Protein,Carbs,Fat\n2026-01-27,Breakfast,Eggs,invalid,12,0,5';
      const file = new File([csvContent], 'nutrition.csv', { type: 'text/csv' });

      const promise = service.uploadMyFitnessPalCSV(file);

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

      const result = await promise;
      expect(result.success).toBe(true);
      expect(result.imported).toBe(5);
      expect(result.errors.length).toBe(1);
    });

    it('should handle validation error (422)', async () => {
      const file = new File(['invalid'], 'invalid.txt', { type: 'text/plain' });
      const promise = service.uploadMyFitnessPalCSV(file);

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      req.flush(
        { detail: 'Invalid CSV format' },
        { status: 422, statusText: 'Unprocessable Entity' }
      );

      try {
        await promise;
        fail('Should have failed');
      } catch (error: any) {
        expect(error.status).toBe(422);
      }
    });

    it('should handle file too large error', async () => {
      const file = new File(['content'], 'large.csv', { type: 'text/csv' });
      const promise = service.uploadMyFitnessPalCSV(file);

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      req.flush(
        { detail: 'File too large' },
        { status: 413, statusText: 'Payload Too Large' }
      );

      try {
        await promise;
        fail('Should have failed');
      } catch (error: any) {
        expect(error.status).toBe(413);
      }
    });

    it('should handle server error (500)', async () => {
      const file = new File(['content'], 'nutrition.csv', { type: 'text/csv' });
      const promise = service.uploadMyFitnessPalCSV(file);

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      req.flush(
        { detail: 'Server error during import' },
        { status: 500, statusText: 'Internal Server Error' }
      );

      try {
        await promise;
        fail('Should have failed');
      } catch (error: any) {
        expect(error.status).toBe(500);
      }
    });

    it('should handle unauthorized error (401)', async () => {
      const file = new File(['content'], 'nutrition.csv', { type: 'text/csv' });
      const promise = service.uploadMyFitnessPalCSV(file);

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      req.flush(
        { detail: 'Unauthorized' },
        { status: 401, statusText: 'Unauthorized' }
      );

      try {
        await promise;
        fail('Should have failed');
      } catch (error: any) {
        expect(error.status).toBe(401);
      }
    });

    it('should send FormData with correct content-type', async () => {
      const file = new File(['content'], 'nutrition.csv', { type: 'text/csv' });
      const promise = service.uploadMyFitnessPalCSV(file);

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      // FormData requests should not set Content-Type (browser sets it with boundary)
      expect(req.request.headers.has('Content-Type')).toBeFalsy();

      // Verify FormData is used
      expect(req.request.body instanceof FormData).toBe(true);

      req.flush({ success: true, imported: 1, skipped: 0, errors: [] });

      const result = await promise;
      expect(result.success).toBe(true);
    });

    it('should handle empty response', async () => {
      const file = new File(['content'], 'nutrition.csv', { type: 'text/csv' });
      const promise = service.uploadMyFitnessPalCSV(file);

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      req.flush({});
      const result = await promise;
      expect(result).toEqual({});
    });

    it('should return promise that can be called multiple times', async () => {
      const file = new File(['content'], 'nutrition.csv', { type: 'text/csv' });

      // First call
      const promise1 = service.uploadMyFitnessPalCSV(file);
      const req1 = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );
      req1.flush({ success: true, imported: 1, skipped: 0, errors: [] });
      const result1 = await promise1;
      expect(result1.success).toBe(true);

      // Second call
      const promise2 = service.uploadMyFitnessPalCSV(file);
      const req2 = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );
      req2.flush({ success: true, imported: 1, skipped: 0, errors: [] });
      const result2 = await promise2;
      expect(result2.success).toBe(true);
    });
  });

  describe('File Types', () => {
    it('should accept various CSV MIME types', async () => {
      const mimeTypes = ['text/csv', 'text/plain', 'application/csv'];

      for (let i = 0; i < mimeTypes.length; i++) {
        const file = new File(['content'], `file_${i}.csv`, { type: mimeTypes[i] });

        const promise = service.uploadMyFitnessPalCSV(file);

        const req = httpMock.expectOne(req =>
          req.url.includes('/nutrition/import/myfitnesspal')
        );

        req.flush({ success: true, imported: 1, skipped: 0, errors: [] });
        const result = await promise;
        expect(result.success).toBe(true);
      }
    });

    it('should preserve original filename in FormData', async () => {
      const filename = 'myfitnesspal_export_2026-01-27.csv';
      const file = new File(['content'], filename, { type: 'text/csv' });

      const promise = service.uploadMyFitnessPalCSV(file);

      const req = httpMock.expectOne(req =>
        req.url.includes('/nutrition/import/myfitnesspal')
      );

      const formData = req.request.body as FormData;
      const uploadedFile = formData.get('file') as File;

      expect(uploadedFile.name).toBe(filename);

      req.flush({ success: true, imported: 1, skipped: 0, errors: [] });
      await promise;
    });
  });
});
