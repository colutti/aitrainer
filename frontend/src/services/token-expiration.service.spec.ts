import { TestBed, fakeAsync, tick, flush } from '@angular/core/testing';
import { TokenExpirationService } from './token-expiration.service';

// Helper para criar token JWT mock
function createMockToken(expiresInSeconds: number): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(JSON.stringify({
    sub: 'test-user',
    exp: Math.floor(Date.now() / 1000) + expiresInSeconds,
    iat: Math.floor(Date.now() / 1000)
  }));
  const signature = 'mock-signature';
  return `${header}.${payload}.${signature}`;
}

describe('TokenExpirationService', () => {
  let service: TokenExpirationService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(TokenExpirationService);
  });

  afterEach(() => {
    service.stopMonitoring();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should decode token and schedule expiration timer', fakeAsync(() => {
    const token = createMockToken(60); // Expira em 60 segundos

    service.startMonitoring(token);

    // Não deve disparar imediatamente
    expect(service.tokenExpired()).toBe(false);

    // Avança 54 segundos (60s - 5s buffer - 1s margem)
    tick(54000);
    expect(service.tokenExpired()).toBe(false);

    // Avança mais 2 segundos (total 56s, passou dos 55s do timer)
    tick(2000);
    expect(service.tokenExpired()).toBe(true);

    flush();
  }));

  it('should detect already expired token', fakeAsync(() => {
    const token = createMockToken(-10); // Token expirado há 10 segundos

    service.startMonitoring(token);

    // Deve marcar como expirado imediatamente
    expect(service.tokenExpired()).toBe(true);

    flush();
  }));

  it('should handle token expiring in less than buffer time', fakeAsync(() => {
    const token = createMockToken(3); // Expira em 3 segundos (menos que buffer de 5s)

    service.startMonitoring(token);

    // Não deve disparar imediatamente
    expect(service.tokenExpired()).toBe(false);

    // Timer deve disparar imediatamente (timerDuration = 0)
    tick(100);
    expect(service.tokenExpired()).toBe(true);

    flush();
  }));

  it('should cancel previous timer when starting new monitoring', fakeAsync(() => {
    const token1 = createMockToken(60);
    const token2 = createMockToken(120);

    service.startMonitoring(token1);
    tick(30000); // 30 segundos

    // Inicia novo monitoramento (deve cancelar timer anterior)
    service.startMonitoring(token2);

    // Avança além do tempo de expiração do token1
    tick(35000); // Total: 65 segundos

    // Não deve ter disparado (timer do token1 foi cancelado)
    expect(service.tokenExpired()).toBe(false);

    flush();
  }));

  it('should stop monitoring and clear timer', fakeAsync(() => {
    const token = createMockToken(60);

    service.startMonitoring(token);
    tick(30000); // 30 segundos

    service.stopMonitoring();

    // Signal deve ser resetado
    expect(service.tokenExpired()).toBe(false);

    // Avança além do tempo de expiração
    tick(40000); // Total: 70 segundos

    // Não deve disparar (timer foi cancelado)
    expect(service.tokenExpired()).toBe(false);

    flush();
  }));

  it('should handle invalid token gracefully', fakeAsync(() => {
    const invalidToken = 'invalid.token.here';

    // Não deve lançar exceção
    expect(() => service.startMonitoring(invalidToken)).not.toThrow();

    // Não deve marcar como expirado
    expect(service.tokenExpired()).toBe(false);

    flush();
  }));

  it('should handle token without exp field', fakeAsync(() => {
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const payload = btoa(JSON.stringify({
      sub: 'test-user',
      iat: Math.floor(Date.now() / 1000)
      // Sem campo exp
    }));
    const tokenWithoutExp = `${header}.${payload}.signature`;

    service.startMonitoring(tokenWithoutExp);

    // Não deve marcar como expirado
    expect(service.tokenExpired()).toBe(false);

    flush();
  }));

});
