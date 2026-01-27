import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { AuthService } from './auth.service';
import { HttpClient, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../environment';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        AuthService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should check localStorage on init', async () => {
    localStorage.setItem('jwt_token', 'test_token');
    
    // We must instantiate the service MANUALLY to test the constructor logic
    const http = TestBed.inject(HttpClient);
    const serviceInstance = new AuthService(http);
    
    // The constructor calls loadUserInfo, which fires a request
    const req = httpMock.expectOne(`${environment.apiUrl}/user/me`);
    expect(req.request.method).toBe('GET');
    req.flush({ email: 'test@test.com', role: 'user' });
    
    // Wait for promise to resolve since we cannot await the constructor
    await new Promise(resolve => setTimeout(resolve, 0));
    
    expect(serviceInstance.isAuthenticated()).toBe(true);
  });

  it('should login successfully', async () => {
    const loginPromise = service.login('test@test.com', 'password');

    const req = httpMock.expectOne(`${environment.apiUrl}/user/login`);
    expect(req.request.method).toBe('POST');
    req.flush({ token: 'new_token' });
    
    // We need to wait for the microtask queue to process the first response
    // which triggers the second request inside the service
    await new Promise(resolve => setTimeout(resolve, 0));
    
    const reqUser = httpMock.expectOne(`${environment.apiUrl}/user/me`);
    expect(reqUser.request.method).toBe('GET');
    reqUser.flush({ email: 'test@test.com', role: 'user' });

    const result = await loginPromise;

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
