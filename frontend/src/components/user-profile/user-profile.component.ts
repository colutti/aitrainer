import { Component, ChangeDetectionStrategy, inject, signal, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { UserProfileService } from '../../services/user-profile.service';
import { UserProfile } from '../../models/user-profile.model';
import { UserProfileInput } from '../../models/user-profile-input.model';

/** Validation error structure returned by the backend */
interface ValidationError {
  loc: string[];
  msg: string;
  type: string;
}

/**
 * Checks if an object is a ValidationError.
 */
function isValidationError(obj: unknown): obj is ValidationError {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'loc' in obj &&
    'msg' in obj &&
    Array.isArray((obj as ValidationError).loc)
  );
}

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
    email: '',
    goal_type: 'maintain',
    weekly_rate: 0.5
  });

  isSaving = signal(false);
  showSuccess = signal(false);
  validationErrors = signal<{ [key: string]: string }>({});

  async ngOnInit(): Promise<void> {
    const loaded = await this.userProfileService.getProfile();
    if (loaded) {
      this.profile.set({ ...loaded });
    }
  }

  onGoalTypeChange(): void {
    if (this.profile().goal_type === 'maintain') {
      const current = this.profile();
      this.profile.set({ ...current, weekly_rate: 0 });
    }
  }

  async saveProfile(): Promise<void> {
    this.isSaving.set(true);
    this.validationErrors.set({});
    this.showSuccess.set(false);

    const profileToUpdate: UserProfileInput = {
      gender: this.profile().gender,
      age: this.profile().age,
      weight: this.profile().weight,
      height: this.profile().height,
      goal: this.profile().goal,
      goal_type: this.profile().goal_type,
      weekly_rate: this.profile().goal_type === 'maintain' ? 0 : this.profile().weekly_rate,
      target_weight: this.profile().target_weight
    };

    try {
      await this.userProfileService.updateProfile(profileToUpdate);
      this.showSuccess.set(true);
      setTimeout(() => this.showSuccess.set(false), 2000);
    } catch (errors: unknown) {
      const errorMap: { [key: string]: string } = {};
      if (Array.isArray(errors)) {
        errors.forEach((err: unknown) => {
          if (isValidationError(err) && err.loc.length > 1) {
            const field = err.loc[1];
            errorMap[field] = err.msg;
          }
        });
      }
      this.validationErrors.set(errorMap);
    } finally {
      this.isSaving.set(false);
    }
  }
}