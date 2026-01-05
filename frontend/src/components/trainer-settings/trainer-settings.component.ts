import { Component, ChangeDetectionStrategy, inject, signal, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { TrainerProfileService } from '../../services/trainer-profile.service';
import { TrainerProfile } from '../../models/trainer-profile.model';

@Component({
  selector: 'app-trainer-settings',
  templateUrl: './trainer-settings.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule]
})
export class TrainerSettingsComponent implements OnInit {
  private trainerProfileService = inject(TrainerProfileService);

  profile = signal<TrainerProfile>(this.trainerProfileService.getProfile());

  isSaving = signal(false);
  showSuccess = signal(false);
  errorMessage = signal('');

  async ngOnInit(): Promise<void> {
    await this.trainerProfileService.fetchProfile();
    this.profile.set(this.trainerProfileService.getProfile());
  }

  async saveProfile(): Promise<void> {
    this.isSaving.set(true);
    this.errorMessage.set('');
    this.showSuccess.set(false);

    try {
      await this.trainerProfileService.updateProfile(this.profile());
      this.showSuccess.set(true);
      setTimeout(() => this.showSuccess.set(false), 3000);
    } catch (err) {
      console.error('Failed to save profile', err);
      this.errorMessage.set('Erro ao salvar o perfil. Tente novamente.');
    } finally {
      this.isSaving.set(false);
    }
  }
}
