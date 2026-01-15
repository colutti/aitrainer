import { Component, inject, OnInit, effect, signal, untracked } from "@angular/core";
import { CommonModule } from "@angular/common";
import { MetabolismService } from "../../services/metabolism.service";
import { UserProfileService } from "../../services/user-profile.service";
import { MarkdownModule } from "ngx-markdown";
import { TrainerProfileService } from '../../services/trainer-profile.service';
import { TrainerCard } from '../../models/trainer-profile.model';

@Component({
  selector: 'app-metabolism',
  standalone: true,
  imports: [CommonModule, MarkdownModule],
  templateUrl: './metabolism.component.html',
})
export class MetabolismComponent implements OnInit {
  metabolismService = inject(MetabolismService);
  userProfileService = inject(UserProfileService);
  trainerService = inject(TrainerProfileService);
  
  stats = this.metabolismService.stats;
  isLoading = this.metabolismService.isLoading;
  profile = this.userProfileService.userProfile;
  
  // New signal to store the resolved trainer card
  currentTrainer = signal<TrainerCard | null>(null);

  insightText = signal<string>('');
  isInsightLoading = signal<boolean>(false);

  constructor() {
      effect(() => {
          const s = this.stats();
          if (s && s.confidence !== 'none') {
             // Use untracked to avoid loops if needed, but here we just react to stats
             untracked(() => {
                 this.streamInsight();
             });
          }
      });
      
      // Update current trainer when profile changes
      effect(async () => {
          const p = this.profile();
          if (p) {
              const trainers = await this.trainerService.getAvailableTrainers();
              // Backend 'get_profile' doesn't return trainer_type directly in UserProfile, 
              // we need to fetch TrainerProfile or assume.
              // Wait, previous messages show UserProfile stores personal data. 
              // Trainer selection is in TrainerProfile endpoint.
              
              // Let's fetch the trainer profile separately to get the type
              const trainerProfile = await this.trainerService.fetchProfile();
              const matched = trainers.find(t => t.trainer_id === trainerProfile.trainer_type);
              
              if (matched) {
                  this.currentTrainer.set(matched);
              }
          }
      });
  }

  ngOnInit() {
    this.metabolismService.fetchSummary(3);
    // Trigger profile load just in case
    this.userProfileService.getProfile();
  }
  
  async streamInsight() {
      if (this.isInsightLoading() || this.insightText()) return; // Already loading or loaded
      
      this.isInsightLoading.set(true);
      this.insightText.set('');
      
      try {
          const reader = await this.metabolismService.getInsightStream();
           const decoder = new TextDecoder();

           while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                this.insightText.update(prev => prev + chunk);
           }
      } catch (err) {
          console.error("Stream error", err);
          this.insightText.set("Não foi possível gerar a análise do treinador no momento.");
      } finally {
          this.isInsightLoading.set(false);
      }
  }

  getRecommendation(): string {
    const s = this.stats();
    if (!s || s.confidence === 'none') return 'Dados insuficientes. Continue logando peso e dieta.';
    return `Sua meta diária recomendada é de ${s.daily_target} kcal para atingir seu objetivo.`;
  }

  getProgressStatus(): { percentage: number, label: string, color: string } {
    const s = this.stats();
    if (!s || !s.goal_weekly_rate || s.goal_weekly_rate === 0) return { percentage: 0, label: '--', color: 'bg-gray-500' };

    const actual = Math.abs(s.weight_change_per_week);
    const goal = Math.abs(s.goal_weekly_rate);
    const percentage = Math.min(100, Math.round((actual / goal) * 100));

    let label = `${percentage}% do objetivo`;
    let color = 'bg-yellow-500';

    if (percentage >= 90) {
      label = "No caminho certo! 🎯";
      color = 'bg-green-500';
    } else if (percentage < 50) {
      label = "Abaixo do esperado";
      color = 'bg-red-500';
    }

    return { percentage, label, color };
  }
  
  getConfidenceColor(level: string): string {
    switch(level) {
        case 'high': return 'text-green-400';
        case 'medium': return 'text-yellow-400';
        case 'low': return 'text-red-400';
        default: return 'text-gray-400';
    }
  }

  getConfidenceColorHex(level: string | undefined): string {
      switch(level) {
          case 'high': return '#4ade80';
          case 'medium': return '#facc15';
          case 'low': return '#f87171';
          default: return '#9ca3af';
      }
  }

  getConfidenceReason(s: any): string {
      if (!s) return 'Dados carregando...';
      if (s.confidence === 'low') {
          return s.confidence_reason || 'Dados inconsistentes.';
      }
      return s.confidence_reason || 'Dados confiáveis.';
  }

  getTotalProgressPercentage(): number {
    const s = this.stats();
    if (!s || !s.target_weight || !s.start_weight) return 0;
    
    const totalToChange = Math.abs(s.start_weight - s.target_weight);
    if (totalToChange === 0) return 100;
    
    const currentChange = Math.abs(s.start_weight - s.latest_weight);
    const percentage = (currentChange / totalToChange) * 100;
    
    return Math.min(100, Math.max(0, percentage));
  }

  getSparklinePath(): string {
    const s = this.stats();
    if (!s || !s.weight_trend || s.weight_trend.length < 2) return '';
    
    const weights = s.weight_trend.map(t => t.weight);
    const min = Math.min(...weights) - 0.5;
    const max = Math.max(...weights) + 0.5;
    const range = max - min;
    
    if (range === 0) return 'M 0 20 L 100 20';
    
    const width = 100;
    const height = 40;
    
    const points = weights.map((w, i) => {
      const x = (i / (weights.length - 1)) * width;
      const y = height - ((w - min) / range) * height;
      return `${x},${y}`;
    });
    
    return `M ${points.join(' L ')}`;
  }
}
