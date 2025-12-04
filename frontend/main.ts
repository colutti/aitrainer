import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient, HTTP_INTERCEPTORS } from '@angular/common/http';
import { AppComponent } from './src/app.component';
import { JwtInterceptor } from './src/services/jwt.interceptor';

bootstrapApplication(AppComponent, {
    providers: [
        provideHttpClient(),
        { provide: HTTP_INTERCEPTORS, useClass: JwtInterceptor, multi: true },
    ],
}).catch((err) => console.error(err));