import { Injectable, signal } from '@angular/core';
import { jwtDecode } from 'jwt-decode';

interface JwtPayload {
  exp?: number;
  iat?: number;
  sub?: string;
}

@Injectable({
  providedIn: 'root'
})
export class TokenExpirationService {
  // Signal emitido quando token expira
  private readonly tokenExpiredSignal = signal<boolean>(false);

  // Referência para cancelar timer
  private expirationTimer: ReturnType<typeof setTimeout> | null = null;

  // Buffer de tempo antes da expiração (5 segundos)
  private readonly EXPIRATION_BUFFER_MS = 5000;

  constructor() {}

  /**
   * Inicia monitoramento de expiração do token
   * @param token - JWT token a ser monitorado
   */
  startMonitoring(token: string): void {
    this.stopMonitoring(); // Cancela timer anterior se existir

    try {
      const decoded = jwtDecode<JwtPayload>(token);

      if (!decoded.exp) {
        console.warn('Token JWT não possui campo exp (expiration)');
        return;
      }

      // exp está em segundos, Date.now() em milissegundos
      const expirationTime = decoded.exp * 1000;
      const currentTime = Date.now();
      const timeUntilExpiration = expirationTime - currentTime;

      // Se token já expirou
      if (timeUntilExpiration <= 0) {
        console.warn('Token JWT já está expirado');
        this.tokenExpiredSignal.set(true);
        return;
      }

      // Agenda verificação com buffer de segurança
      const timerDuration = Math.max(0, timeUntilExpiration - this.EXPIRATION_BUFFER_MS);

      console.log(`Token expira em ${Math.floor(timeUntilExpiration / 1000)}s. Timer agendado para ${Math.floor(timerDuration / 1000)}s`);

      this.expirationTimer = setTimeout(() => {
        console.log('Token expirado - disparando signal');
        this.tokenExpiredSignal.set(true);
      }, timerDuration);

    } catch (error) {
      console.error('Erro ao decodificar token JWT:', error);
    }
  }

  /**
   * Para monitoramento e cancela timer pendente
   */
  stopMonitoring(): void {
    if (this.expirationTimer) {
      clearTimeout(this.expirationTimer);
      this.expirationTimer = null;
    }
    this.tokenExpiredSignal.set(false);
  }

  /**
   * Retorna signal de expiração (somente leitura)
   */
  get tokenExpired() {
    return this.tokenExpiredSignal.asReadonly();
  }
}
