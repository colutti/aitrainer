import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WeightService } from '../../../services/weight.service';
import { UserProfileService } from '../../../services/user-profile.service';

@Component({
  selector: 'app-weight-widget',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './weight-widget.component.html',
  styleUrls: ['./weight-widget.component.css']
})
export class WeightWidgetComponent {
  private weightService = inject(WeightService);
  private userProfileService = inject(UserProfileService);

  weightInput = signal<number | null>(null);
  isSaving = signal<boolean>(false);
  lastSaved = this.weightService.lastSaved;
  
  // Quick add buttons relative to last known weight
  suggestion = signal<number | null>(null);

  constructor() {
    // Determine suggestion based on profile weight or history
    const profile = this.userProfileService.userProfile();
    if (profile) {
      this.weightInput.set(profile.weight);
    }
  }

  async saveWeight() {
    if (!this.weightInput()) return;
    
    this.isSaving.set(true);
    try {
      await this.weightService.logWeight(this.weightInput()!);
      // Update local profile weight as well to keep in sync visually
      // Ideally backend updates profile on weight log, or we fetch again.
      // For now, let's just log it. 
      // Actually, we should probably update the user profile service if the weight changed significantly?
      // Or just let the profile be separate. TDEE depends on logs.
    } finally {
      this.isSaving.set(false);
    }
  }
}
