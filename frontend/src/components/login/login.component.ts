
import { Component, ChangeDetectionStrategy, signal, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule],
})
export class LoginComponent {
  private authService = inject(AuthService);

  email = signal('cliente@email.com');
  password = signal('senha123');
  isLoading = signal(false);
  error = signal('');

  async login(): Promise<void> {
    if (this.isLoading()) return;

    this.isLoading.set(true);
    this.error.set('');
    
    try {
      const success = await this.authService.login(this.email(), this.password());
      if (!success) {
        this.error.set('Credenciais inválidas. Tente novamente.');
      }
    } catch (e) {
      this.error.set('Ocorreu um erro. Tente novamente mais tarde.');
    } finally {
      this.isLoading.set(false);
    }
  }
}
