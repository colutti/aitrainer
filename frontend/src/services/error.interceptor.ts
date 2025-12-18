import { Injectable } from '@angular/core';
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

@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
  constructor(private authService: AuthService) { }

  intercept(
    req: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {
    return next.handle(req).pipe(
      catchError((error: HttpErrorResponse) => {
        // Don't auto-logout on the login endpoint itself - let the component handle it
        const isLoginEndpoint = req.url.includes('/user/login');

        if (error.status === 401 && !isLoginEndpoint) {
          // Auto logout if 401 response returned from api
          this.authService.logout();
          // The page will automatically reload and show the login screen
          // because the isAuthenticated signal will become false.
          location.reload();
        }

        // Return the original error to preserve validation details
        return throwError(() => error);
      })
    );
  }
}
