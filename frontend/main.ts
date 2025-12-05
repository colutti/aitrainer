import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient, HTTP_INTERCEPTORS, withInterceptorsFromDi } from '@angular/common/http'; // <--- Importe isso
import { AppComponent } from './src/app.component';
import { JwtInterceptor } from './src/services/jwt.interceptor';

bootstrapApplication(AppComponent, {
    providers: [
        // Adicione withInterceptorsFromDi() aqui dentro
        provideHttpClient(withInterceptorsFromDi()),

        { provide: HTTP_INTERCEPTORS, useClass: JwtInterceptor, multi: true },
    ],
}).catch((err) => console.error(err));