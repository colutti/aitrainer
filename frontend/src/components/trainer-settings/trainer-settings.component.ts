import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TrainerProfileService } from '../../services/trainer-profile.service';
import { NotificationService } from '../../services/notification.service';
import { TrainerProfile, TrainerCard } from '../../models/trainer-profile.model';

@Component({
  selector: 'app-trainer-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './trainer-settings.component.html',
})
export class TrainerSettingsComponent implements OnInit {
  private trainerProfileService = inject(TrainerProfileService);
  private notificationService = inject(NotificationService);

  profile = signal<TrainerProfile>({ trainer_type: 'atlas' });
  availableTrainers = signal<TrainerCard[]>([]);
  
  isSaving = signal(false);

  async ngOnInit() {
    await this.loadTrainers();
    await this.loadProfile();
  }

  async loadTrainers(): Promise<void> {
    try {
        const trainers = await this.trainerProfileService.getAvailableTrainers();
        this.availableTrainers.set(trainers);
    } catch (err) {
        this.notificationService.error('Erro ao carregar treinadores disponíveis.');
    }
  }

  async loadProfile() {
    try {
      const p = await this.trainerProfileService.fetchProfile();
      this.profile.set(p);
    } catch (err) {
    }
  }

  selectTrainer(trainerId: string) {
    this.profile.update(p => ({ ...p, trainer_type: trainerId }));
  }

  async saveProfile() {
    this.isSaving.set(true);

    try {
      const updated = await this.trainerProfileService.updateProfile(this.profile());
      this.profile.set(updated);
      this.notificationService.success('Treinador atualizado com sucesso!');
    } catch (err) {
      this.notificationService.error('Erro ao salvar alterações. Tente novamente.');
    } finally {
      this.isSaving.set(false);
    }
  }
}
