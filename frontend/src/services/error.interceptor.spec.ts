import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { HTTP_INTERCEPTORS, HttpClient } from '@angular/common/http';
import { ErrorInterceptor } from './error.interceptor';
import { AuthService } from './auth.service';
import { NotificationService } from './notification.service';

describe('ErrorInterceptor', () => {
  let httpMock: HttpTestingController;
  let httpClient: HttpClient;
  let authServiceSpy: Partial<AuthService>;
  let notificationServiceSpy: Partial<NotificationService>;

  beforeEach(() => {
    authServiceSpy = { logout: jest.fn() };
    notificationServiceSpy = { error: jest.fn() };

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        { provide: NotificationService, useValue: notificationServiceSpy },
        {
          provide: HTTP_INTERCEPTORS,
          useClass: ErrorInterceptor,
          multi: true,
        },
      ],
    });

    httpMock = TestBed.inject(HttpTestingController);
    httpClient = TestBed.inject(HttpClient);
    ErrorInterceptor.resetThrottle();
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should logout and notify on 401 error', () => {
    httpClient.get('/api/data').subscribe({
      next: () => fail('should have failed with 401 error'),
      error: (error) => {
        expect(error.status).toBe(401);
      },
    });

    const req = httpMock.expectOne('/api/data');
    req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

    expect(authServiceSpy.logout).toHaveBeenCalled();
    expect(notificationServiceSpy.error).toHaveBeenCalledWith('Sessão expirada. Faça login novamente.');
  });

  it('should notify on 403 error', () => {
    httpClient.get('/api/admin').subscribe({
      next: () => fail('should have failed with 403 error'),
      error: (error) => {
        expect(error.status).toBe(403);
      },
    });

    const req = httpMock.expectOne('/api/admin');
    req.flush('Forbidden', { status: 403, statusText: 'Forbidden' });

    expect(notificationServiceSpy.error).toHaveBeenCalledWith('Acesso negado.');
  });

  it('should notify on 429 error', () => {
    httpClient.get('/api/login').subscribe({
      next: () => fail('should have failed with 429 error'),
      error: (error) => {
        expect(error.status).toBe(429);
      },
    });

    const req = httpMock.expectOne('/api/login');
    req.flush('Too Many Requests', { status: 429, statusText: 'Too Many Requests' });

    expect(notificationServiceSpy.error).toHaveBeenCalledWith('Muitas requisições. Aguarde um momento.');
  });

  it('should notify on 500 server error', () => {
    httpClient.get('/api/crash').subscribe({
      next: () => fail('should have failed with 500 error'),
      error: (error) => {
        expect(error.status).toBe(500);
      },
    });

    const req = httpMock.expectOne('/api/crash');
    req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });

    expect(notificationServiceSpy.error).toHaveBeenCalledWith('Erro no servidor. Tente novamente mais tarde.');
  });

    it('should notify on 0 network error', () => {
    httpClient.get('/api/nowhere').subscribe({
      next: () => fail('should have failed with 0 error'),
      error: (error) => {
        expect(error.status).toBe(0);
      },
    });

    const req = httpMock.expectOne('/api/nowhere');
    // Simulate network error
    const mockError = new ProgressEvent('error');
    req.error(mockError);

    expect(notificationServiceSpy.error).toHaveBeenCalledWith('Erro de conexão. Verifique sua internet.');
  });

  it('should NOT logout on 401 during login', () => {
    httpClient.post('/user/login', {}).subscribe({
      next: () => fail('should have failed with 401 error'),
      error: (error) => {
        expect(error.status).toBe(401);
      },
    });

    const req = httpMock.expectOne('/user/login');
    req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

    expect(authServiceSpy.logout).not.toHaveBeenCalled();
    // Notification might still happen depending on implementation, 
    // but the key requirement is NOT logging out recursively.
    // In our implementation we check !isLoginEndpoint for both logout AND notification.
    expect(notificationServiceSpy.error).not.toHaveBeenCalled(); 
  });

  it('should only notify ONCE and logout ONCE on simultaneous 401 errors', () => {
    // Request 1
    httpClient.get('/api/data1').subscribe({
      error: (error) => expect(error.status).toBe(401)
    });

    // Request 2
    httpClient.get('/api/data2').subscribe({
      error: (error) => expect(error.status).toBe(401)
    });

    const req1 = httpMock.expectOne('/api/data1');
    const req2 = httpMock.expectOne('/api/data2');

    req1.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });
    req2.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

    expect(authServiceSpy.logout).toHaveBeenCalledTimes(1);
    expect(notificationServiceSpy.error).toHaveBeenCalledTimes(1);
    expect(notificationServiceSpy.error).toHaveBeenCalledWith('Sessão expirada. Faça login novamente.');
  });
});
