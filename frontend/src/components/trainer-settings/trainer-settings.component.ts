
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

  ngOnInit(): void {
    // Se quiser garantir atualização futura, pode manter o set aqui, mas não é mais necessário
    // this.profile.set({ ...this.trainerProfileService.getProfile() });
  }

  async saveProfile(): Promise<void> {
    this.isSaving.set(true);
    const success = await this.trainerProfileService.updateProfile(this.profile());
    this.isSaving.set(false);
    if (success) {
      this.showSuccess.set(true);
      setTimeout(() => this.showSuccess.set(false), 2000);
    }
  }
}
