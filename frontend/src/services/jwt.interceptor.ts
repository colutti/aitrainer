import { Injectable, inject } from '@angular/core';
import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';

@Injectable()
export class JwtInterceptor implements HttpInterceptor {
    private authService = inject(AuthService);

    intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        const token = this.authService.getToken();
        // Logging para depuração
        console.log('[JWT Interceptor] Token:', token);
        console.log('[JWT Interceptor] URL:', req.url);
        if (token) {
            const cloned = req.clone({
                setHeaders: {
                    Authorization: `Bearer ${token}`,
                },
            });
            console.log('[JWT Interceptor] Headers:', cloned.headers);
            return next.handle(cloned);
        }
        return next.handle(req);
    }
}
