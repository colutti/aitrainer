
import { Injectable, signal, effect } from '@angular/core';
import { TrainerProfile } from '../models/trainer-profile.model';
import { HttpClient } from '@angular/common/http';
import { environment } from '../environment';
import { firstValueFrom } from 'rxjs';

const DEFAULT_TRAINER_PROFILE: TrainerProfile = {
  name: 'Atlas',
  gender: 'Masculino',
  humour: 'Motivacional',
  style: 'Científico',
};

@Injectable({
  providedIn: 'root',
})
export class TrainerProfileService {
  trainerProfile = signal<TrainerProfile>(DEFAULT_TRAINER_PROFILE);

  constructor(private http: HttpClient) {
    const storedProfile = localStorage.getItem('trainer_profile');
    if (storedProfile) {
      const parsed: TrainerProfile = JSON.parse(storedProfile);
      // Preenche campos vazios com valores padrão
      this.trainerProfile.set({
        name: parsed.name || DEFAULT_TRAINER_PROFILE.name,
        gender: parsed.gender || DEFAULT_TRAINER_PROFILE.gender,
        humour: parsed.humour || DEFAULT_TRAINER_PROFILE.humour,
        style: parsed.style || DEFAULT_TRAINER_PROFILE.style,
      });
    }

    effect(() => {
      localStorage.setItem('trainer_profile', JSON.stringify(this.trainerProfile()));
    });
  }

  /**
   * Salva o perfil do treinador no backend
   */
  async updateProfile(profile: TrainerProfile): Promise<void> {
    try {
      await firstValueFrom(this.http.post(`${environment.apiUrl}/update_trainer_profile`, profile));
      this.trainerProfile.set(profile);
    } catch (err) {
      console.error('Erro ao salvar perfil do treinador:', err);
    }
  }

  /**
   * Obtém o perfil do treinador do backend
   */
  async fetchProfile(): Promise<void> {
    try {
      const profile = await firstValueFrom(
        this.http.get<TrainerProfile>(`${environment.apiUrl}/trainer_profile`)
      );
      this.trainerProfile.set(profile);
    } catch (err) {
      console.error('Erro ao obter perfil do treinador:', err);
    }
  }

  getProfile(): TrainerProfile {
    return this.trainerProfile();
  }
}