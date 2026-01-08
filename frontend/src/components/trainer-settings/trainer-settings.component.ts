import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TrainerProfileService } from '../../services/trainer-profile.service';
import { TrainerProfile, TrainerCard } from '../../models/trainer-profile.model';

@Component({
  selector: 'app-trainer-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './trainer-settings.component.html',
})
export class TrainerSettingsComponent implements OnInit {
  private trainerProfileService = inject(TrainerProfileService);

  profile = signal<TrainerProfile>({ trainer_type: 'atlas' });
  availableTrainers = signal<TrainerCard[]>([]);
  
  isSaving = signal(false);
  errorMessage = signal('');
  showSuccess = signal(false);

  async ngOnInit() {
    await this.loadTrainers();
    await this.loadProfile();
  }

  async loadTrainers(): Promise<void> {
    console.log('DEBUG: calling loadTrainers');
    try {
        const trainers = await this.trainerProfileService.getAvailableTrainers();
        console.log('DEBUG: trainers loaded', trainers);
        this.availableTrainers.set(trainers);
    } catch (err) {
        console.error('DEBUG: Failed to load trainers', err);
        this.errorMessage.set('Erro ao carregar treinadores disponíveis.');
    }
  }

  async loadProfile() {
    try {
      const p = await this.trainerProfileService.fetchProfile();
      this.profile.set(p);
    } catch (err) {
      console.error('Error loading profile', err);
    }
  }

  selectTrainer(trainerId: string) {
    this.profile.update(p => ({ ...p, trainer_type: trainerId }));
  }

  async saveProfile() {
    this.isSaving.set(true);
    this.errorMessage.set('');
    this.showSuccess.set(false);

    try {
      const updated = await this.trainerProfileService.updateProfile(this.profile());
      this.profile.set(updated);
      this.showSuccess.set(true);
      setTimeout(() => this.showSuccess.set(false), 3000);
    } catch (err) {
      console.error('Failed to save profile', err);
      this.errorMessage.set('Erro ao salvar alterações. Tente novamente.');
    } finally {
      this.isSaving.set(false);
    }
  }
}
