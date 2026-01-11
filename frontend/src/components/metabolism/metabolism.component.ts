import { Component, inject, OnInit, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MetabolismService } from '../../services/metabolism.service';
import { UserProfileService } from '../../services/user-profile.service';

@Component({
  selector: 'app-metabolism',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './metabolism.component.html',
})
export class MetabolismComponent implements OnInit {
  metabolismService = inject(MetabolismService);
  userProfileService = inject(UserProfileService);
  
  stats = this.metabolismService.stats;
  isLoading = this.metabolismService.isLoading;
  profile = this.userProfileService.userProfile;

  ngOnInit() {
    this.metabolismService.fetchSummary(3);
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

  getInsightText(): string {
    const s = this.stats();
    if (!s || s.confidence === 'none') return '';

    const diff = s.daily_target - s.avg_calories;
    const action = diff > 0 ? "aumentar" : "reduzir";
    const absDiff = Math.abs(diff);

    if (s.is_stable) {
        return `Seu TDEE é de ${s.tdee} kcal. Você está consumindo ${s.avg_calories} kcal em média, o que está mantendo seu peso estável.`;
    }

    const messagePrefix = s.energy_balance < 0 
        ? `Seu TDEE é de ${s.tdee} kcal. Com uma média de ${s.avg_calories} kcal, você está em um déficit real de ${Math.abs(s.energy_balance)} kcal.`
        : `Seu TDEE é de ${s.tdee} kcal. Com uma média de ${s.avg_calories} kcal, você está em um superávit real de ${s.energy_balance} kcal.`;

    return `${messagePrefix} Isso resultou em uma variação de ${s.weight_change_per_week} kg/semana. Para atingir sua meta, sugerimos as recomendações acima.`;
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
