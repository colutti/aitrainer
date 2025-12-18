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

/**
 * HTTP interceptor that handles authentication errors globally.
 * Automatically logs out the user and reloads the page on 401 responses,
 * except for the login endpoint which handles its own errors.
 */
@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
  private authService = inject(AuthService);

  /**
   * Intercepts HTTP responses to handle authentication errors.
   * @param req - The outgoing HTTP request
   * @param next - The next handler in the chain
   * @returns Observable of the HTTP event
   */
  intercept(
    req: HttpRequest<unknown>,
    next: HttpHandler
  ): Observable<HttpEvent<unknown>> {
    return next.handle(req).pipe(
      catchError((error: HttpErrorResponse) => {
        const isLoginEndpoint = req.url.includes('/user/login');

        if (error.status === 401 && !isLoginEndpoint) {
          this.authService.logout();
          location.reload();
        }

        return throwError(() => error);
      })
    );
  }
}

