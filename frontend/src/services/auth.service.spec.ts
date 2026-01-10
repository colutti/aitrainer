import { TestBed } from '@angular/core/testing';
import { AuthService } from './auth.service';
import { HttpClient, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../environment';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        AuthService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
    localStorage.clear();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should check localStorage on init', () => {
    localStorage.setItem('jwt_token', 'test_token');
    // Manually instantiate to trigger constructor logic since TestBed keeps singleton
    const http = TestBed.inject(HttpClient);
    const newService = new AuthService(http);
    expect(newService.isAuthenticated()).toBe(true);
  });

  it('should login successfully', async () => {
    const promise = service.login('test@test.com', 'password');

    const req = httpMock.expectOne(`${environment.apiUrl}/user/login`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ email: 'test@test.com', password: 'password' });
    req.flush({ token: 'new_token' });

    const result = await promise;

    expect(result).toBe(true);
    expect(service.isAuthenticated()).toBe(true);
    expect(localStorage.getItem('jwt_token')).toBe('new_token');
  });

  it('should handle login failure', async () => {
    const promise = service.login('test@test.com', 'wrong');

    const req = httpMock.expectOne(`${environment.apiUrl}/user/login`);
    req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

    const result = await promise;

    expect(result).toBe(false);
    expect(service.isAuthenticated()).toBe(false);
    expect(localStorage.getItem('jwt_token')).toBeNull();
  });

  it('should logout successfully', async () => {
    service.isAuthenticated.set(true);
    localStorage.setItem('jwt_token', 'token');

    const promise = service.logout();

    const req = httpMock.expectOne(`${environment.apiUrl}/user/logout`);
    expect(req.request.method).toBe('POST');
    req.flush({});

    await promise;

    expect(service.isAuthenticated()).toBe(false);
    expect(localStorage.getItem('jwt_token')).toBeNull();
  });
});
