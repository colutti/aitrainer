import { Component, inject, OnInit, effect, signal, untracked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MetabolismService } from '../../services/metabolism.service';
import { UserProfileService } from '../../services/user-profile.service';
import { MarkdownModule } from 'ngx-markdown';

@Component({
  selector: 'app-metabolism',
  standalone: true,
  imports: [CommonModule, MarkdownModule],
  templateUrl: './metabolism.component.html',
})
export class MetabolismComponent implements OnInit {
  metabolismService = inject(MetabolismService);
  userProfileService = inject(UserProfileService);
  
  stats = this.metabolismService.stats;
  isLoading = this.metabolismService.isLoading;
  profile = this.userProfileService.userProfile;

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
  }

  ngOnInit() {
    this.metabolismService.fetchSummary(3);
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
}
