import { TestBed, ComponentFixture, fakeAsync, tick } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { AppComponent } from './app.component';
import { AuthService } from './services/auth.service';
import { TokenExpirationService } from './services/token-expiration.service';
import { NavigationService } from './services/navigation.service';

describe('AppComponent - Token Expiration Effect', () => {
  let component: AppComponent;
  let fixture: ComponentFixture<AppComponent>;
  let authService: AuthService;
  let tokenService: TokenExpirationService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, AppComponent],
      providers: [AuthService, TokenExpirationService, NavigationService]
    }).compileComponents();

    fixture = TestBed.createComponent(AppComponent);
    component = fixture.componentInstance;
    authService = TestBed.inject(AuthService);
    tokenService = TestBed.inject(TokenExpirationService);

    // Mock inicial - usuário autenticado
    authService.isAuthenticated.set(true);
  });

  afterEach(() => {
    tokenService.stopMonitoring();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have token expiration service injected', () => {
    expect(component.tokenExpirationService).toBeTruthy();
  });

  it('should have authentication service injected', () => {
    expect(component.authService).toBeTruthy();
  });
});
