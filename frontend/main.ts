import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient, HTTP_INTERCEPTORS, withInterceptorsFromDi } from '@angular/common/http';
import { provideMarkdown } from 'ngx-markdown';
import { AppComponent } from './src/app.component';
import { JwtInterceptor } from './src/services/jwt.interceptor';
import { ErrorInterceptor } from './src/services/error.interceptor';

bootstrapApplication(AppComponent, {
    providers: [
        // Adicione withInterceptorsFromDi() aqui dentro
        provideHttpClient(withInterceptorsFromDi()),
        provideMarkdown(),

        { provide: HTTP_INTERCEPTORS, useClass: JwtInterceptor, multi: true },
        { provide: HTTP_INTERCEPTORS, useClass: ErrorInterceptor, multi: true },
    ],
}).catch((err) => console.error(err));