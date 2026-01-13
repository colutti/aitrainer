import { Injectable, inject } from '@angular/core';
import {
  HttpEvent,
  HttpInterceptor,
  HttpHandler,
  HttpRequest,
  HttpErrorResponse,
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { AuthService } from './auth.service';
import { NotificationService } from './notification.service';

/**
 * HTTP interceptor that handles authentication errors globally.
 * Automatically logs out the user and reloads the page on 401 responses,
 * except for the login endpoint which handles its own errors.
 */
@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
  private authService = inject(AuthService);
  private notificationService = inject(NotificationService);

  intercept(
    req: HttpRequest<unknown>,
    next: HttpHandler
  ): Observable<HttpEvent<unknown>> {
    return next.handle(req).pipe(
      catchError((error: HttpErrorResponse) => {
        const isLoginEndpoint = req.url.includes('/user/login');
        const isLogoutEndpoint = req.url.includes('/user/logout');

        // 401: Unauthorized (handled by checking endpoints to avoid loops)
        if (error.status === 401 && !isLoginEndpoint && !isLogoutEndpoint) {
          this.authService.logout();
          this.notificationService.error('Sessão expirada. Faça login novamente.');
        }
        
        // 403: Forbidden
        else if (error.status === 403) {
            this.notificationService.error('Acesso negado.');
        }

        // 429: Rate Limit
        else if (error.status === 429) {
            this.notificationService.error('Muitas requisições. Aguarde um momento.');
        }

        // 5xx: Server Errors
        else if (error.status >= 500) {
            this.notificationService.error('Erro no servidor. Tente novamente mais tarde.');
        }

        // 0: Network Error (Unknown)
        else if (error.status === 0) {
            this.notificationService.error('Erro de conexão. Verifique sua internet.');
        }
        
        // Use backend error message if available and reasonable to show (e.g. 400 Bad Request)
        // We generally rely on the component to handle specific 400 validation errors, 
        // but checking for specific "detail" strings could be useful here if standardized.

        return throwError(() => error);
      })
    );
  }
}

