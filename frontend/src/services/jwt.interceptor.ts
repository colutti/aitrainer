import { Injectable, inject } from '@angular/core';
import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';

/**
 * HTTP interceptor that attaches JWT token to outgoing requests.
 * Automatically adds Authorization header with Bearer token when user is authenticated.
 */
@Injectable()
export class JwtInterceptor implements HttpInterceptor {
    private authService = inject(AuthService);

    /**
     * Intercepts HTTP requests and adds JWT token if available.
     * @param req - The outgoing HTTP request
     * @param next - The next handler in the chain
     * @returns Observable of the HTTP event
     */
    intercept(req: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
        const token = this.authService.getToken();
        if (token) {
            const cloned = req.clone({
                setHeaders: {
                    Authorization: `Bearer ${token}`,
                },
            });
            return next.handle(cloned);
        }
        return next.handle(req);
    }
}

