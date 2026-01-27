import { Component, OnInit, signal, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { OnboardingService, OnboardingData } from '../../services/onboarding.service';
import { AuthService } from '../../services/auth.service';
import { NavigationService } from '../../services/navigation.service';
import { NumberInputComponent } from '../shared/number-input/number-input.component';

type Step = 1 | 2 | 3;

interface FormData {
  password: string;
  confirmPassword: string;
  gender: 'Masculino' | 'Feminino';
  age: number;
  weight: number;
  height: number;
  goal_type: 'lose' | 'gain' | 'maintain';
  weekly_rate: number;
  trainer_type: 'atlas' | 'luna' | 'sargento' | 'sofia';
}

@Component({
  selector: 'app-onboarding',
  templateUrl: './onboarding.component.html',
  styleUrls: ['./onboarding.component.css'],
  standalone: true,
  imports: [CommonModule, FormsModule, NumberInputComponent],
})
export class OnboardingComponent implements OnInit {
  private onboardingService = inject(OnboardingService);
  private authService = inject(AuthService);
  private navigationService = inject(NavigationService);

  currentStep = signal<Step>(1);
  token = signal<string>('');
  email = signal<string>('');
  isLoading = signal(false);
  error = signal('');

  formData = signal<FormData>({
    password: '',
    confirmPassword: '',
    gender: 'Masculino',
    age: 25,
    weight: 70,
    height: 170,
    goal_type: 'maintain',
    weekly_rate: 0.5,
    trainer_type: 'atlas'
  });

  // Computed signals
  passwordsMatch = computed(() => {
    const data = this.formData();
    return data.password === data.confirmPassword;
  });

  canProceedStep1 = computed(() => {
    const data = this.formData();
    const password = data.password;
    const hasLower = /[a-z]/.test(password);
    const hasUpper = /[A-Z]/.test(password);
    const hasDigit = /[0-9]/.test(password);
    const isLongEnough = password.length >= 8;
    
    return isLongEnough && hasLower && hasUpper && hasDigit && this.passwordsMatch();
  });

  canProceedStep2 = computed(() => {
    const data = this.formData();
    return data.age >= 18 && data.weight > 0 && data.height > 0;
  });

  async ngOnInit() {
    // Get token from URL manually since router is not available
    const urlParams = new URLSearchParams(window.location.search);
    const tokenParam = urlParams.get('token');
    
    if (!tokenParam) {
      this.error.set('Token de convite não encontrado');
      return;
    }

    this.token.set(tokenParam);

    // Validate token
    this.isLoading.set(true);
    try {
      const result = await this.onboardingService.validateToken(tokenParam);
      
      if (!result.valid) {
        this.handleInvalidToken(result.reason || 'unknown');
        return;
      }

      this.email.set(result.email || '');
      
      // Try to restore from localStorage
      this.restoreFormData();
    } catch {
      this.error.set('Erro ao validar convite. Tente novamente.');
    } finally {
      this.isLoading.set(false);
    }
  }

  private handleInvalidToken(reason: string) {
    const messages: Record<string, string> = {
      'not_found': 'Convite não encontrado',
      'expired': 'Este convite expirou. Solicite um novo.',
      'already_used': 'Este convite já foi utilizado. Você já possui uma conta?'
    };
    this.error.set(messages[reason] || 'Convite inválido');
  }

  private restoreFormData() {
    const saved = localStorage.getItem(`onboarding_${this.token()}`);
    if (saved) {
      try {
        const data = JSON.parse(saved);
        // Don't restore password for security
        delete data.password;
        delete data.confirmPassword;
        this.formData.set({ ...this.formData(), ...data });
      } catch {
        // Ignore parse errors
      }
    }
  }

  private saveFormData() {
    const data = { ...this.formData() };
    // Don't save passwords
    delete data.password;
    delete data.confirmPassword;
    localStorage.setItem(`onboarding_${this.token()}`, JSON.stringify(data));
  }

  nextStep() {
    const current = this.currentStep();
    if (current < 3) {
      this.saveFormData();
      this.currentStep.set((current + 1) as Step);
    }
  }

  previousStep() {
    const current = this.currentStep();
    if (current > 1) {
      this.currentStep.set((current - 1) as Step);
    }
  }

  updateFormData(field: keyof FormData, value: string | number) {
    this.formData.update(data => ({ ...data, [field]: value }));
  }

  async complete() {
    if (this.isLoading()) return;

    this.isLoading.set(true);
    this.error.set('');

    try {
      const data: OnboardingData = {
        token: this.token(),
        password: this.formData().password,
        gender: this.formData().gender,
        age: this.formData().age,
        weight: this.formData().weight,
        height: this.formData().height,
        goal_type: this.formData().goal_type,
        weekly_rate: this.formData().weekly_rate,
        trainer_type: this.formData().trainer_type
      };

      const response = await this.onboardingService.completeOnboarding(data);
      
      // Save token and login
      localStorage.setItem('jwt_token', response.token);
      localStorage.removeItem(`onboarding_${this.token()}`);
      
      // Update auth state in service if necessary
      this.authService.isAuthenticated.set(true);
      
      // Clear URL params and reload to dashboard

      window.history.replaceState({}, document.title, window.location.pathname);
      window.location.href = '/'; // Hard redirect to clear all states and enter dashboard
      
    } catch (error: unknown) {
      const err = error as { status?: number };
      if (err.status === 410) {
        this.error.set('Seu convite expirou. Solicite um novo.');
      } else if (err.status === 409) {
        this.error.set('Este convite já foi utilizado.');
      } else {
        this.error.set('Erro ao criar conta. Tente novamente.');
      }
    } finally {
      this.isLoading.set(false);
    }
  }
}
