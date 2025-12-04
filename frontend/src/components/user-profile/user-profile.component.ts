
import { Component, ChangeDetectionStrategy, inject, signal, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { UserProfileService } from '../../services/user-profile.service';
import { UserProfile } from '../../models/user-profile.model';

@Component({
  selector: 'app-user-profile',
  templateUrl: './user-profile.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule]
})
export class UserProfileComponent implements OnInit {
  private userProfileService = inject(UserProfileService);

  profile = signal<UserProfile>({
    gender: '',
    age: 0,
    weight: 0,
    height: 0,
    goal: '',
    email: ''
  });

  isSaving = signal(false);
  showSuccess = signal(false);

  async ngOnInit(): Promise<void> {
    const loaded = await this.userProfileService.getProfile();
    if (loaded) {
      this.profile.set({ ...loaded });
    }
  }

  async saveProfile(): Promise<void> {
    this.isSaving.set(true);
    const success = await this.userProfileService.updateProfile(this.profile());
    this.isSaving.set(false);
    if (success) {
      this.showSuccess.set(true);
      setTimeout(() => this.showSuccess.set(false), 2000);
    }
  }
}
