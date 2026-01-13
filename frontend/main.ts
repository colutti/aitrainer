import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient, HTTP_INTERCEPTORS, withInterceptorsFromDi } from '@angular/common/http';
import { provideMarkdown } from 'ngx-markdown';
import { provideCharts, withDefaultRegisterables } from 'ng2-charts';
import { AppComponent } from './src/app.component';
import { JwtInterceptor } from './src/services/jwt.interceptor';
import { ErrorInterceptor } from './src/services/error.interceptor';

import { registerLocaleData } from '@angular/common';
import localePtBr from '@angular/common/locales/pt';
import { LOCALE_ID } from '@angular/core';

registerLocaleData(localePtBr, 'pt');
registerLocaleData(localePtBr, 'pt-BR');

bootstrapApplication(AppComponent, {
    providers: [
        // Adicione withInterceptorsFromDi() aqui dentro
        provideHttpClient(withInterceptorsFromDi()),
        provideMarkdown(),
        provideCharts(withDefaultRegisterables()),
        { provide: LOCALE_ID, useValue: 'pt-BR' },

        { provide: HTTP_INTERCEPTORS, useClass: JwtInterceptor, multi: true },
        { provide: HTTP_INTERCEPTORS, useClass: ErrorInterceptor, multi: true },
    ],
}).catch((err) => console.error(err));