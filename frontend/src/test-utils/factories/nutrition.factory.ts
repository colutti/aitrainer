import { NutritionLog, NutritionStats } from '../../models/nutrition.model';

export class NutritionFactory {
  static createLog(overrides?: Partial<NutritionLog>): NutritionLog {
    return {
      id: 'log_' + Date.now(),
      user_email: 'test@example.com',
      date: new Date().toISOString().split('T')[0],
      source: 'Manual',
      calories: 600,
      protein_grams: 30,
      carbs_grams: 80,
      fat_grams: 20,
      ...overrides
    } as NutritionLog;
  }

  static createLogList(count: number, startDaysAgo: number = 0): NutritionLog[] {
    return Array.from({ length: count }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (startDaysAgo + i));
      return this.createLog({
        id: `log_${i}`,
        date: date.toISOString().split('T')[0],
        calories: 1800 + Math.random() * 400,
        protein_grams: 120 + Math.random() * 30,
        carbs_grams: 200 + Math.random() * 40,
        fat_grams: 60 + Math.random() * 20
      });
    });
  }

  static createDayMacros(overrides?: any): any {
    return {
      date: new Date().toISOString().split('T')[0],
      calories: 2000,
      protein: 150,
      carbs: 200,
      fat: 60,
      ...overrides
    };
  }

  static createDayMacrosList(count: number): any[] {
    return Array.from({ length: count }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - i);
      return this.createDayMacros({
        date: date.toISOString().split('T')[0]
      });
    });
  }

  static createStats(overrides?: Partial<NutritionStats>): NutritionStats {
    const stats: NutritionStats = {
      today: this.createLog(),
      weekly_adherence: [true, false, true, true, false, true, true],
      last_7_days: this.createDayMacrosList(7),
      last_14_days: this.createDayMacrosList(14),
      avg_daily_calories: 2100,
      avg_daily_calories_14_days: 2050,
      avg_protein: 145,
      total_logs: 50,
      macro_targets: { protein: 150, carbs: 250, fat: 70 },
      daily_target: 2200,
      stability_score: 85,
      ...overrides
    };
    return stats;
  }

  static createBreakfast(): NutritionLog {
    return this.createLog({
      source: 'Manual',
      calories: 600,
      protein_grams: 30,
      carbs_grams: 80,
      fat_grams: 20
    });
  }

  static createLunch(): NutritionLog {
    return this.createLog({
      source: 'Manual',
      calories: 850,
      protein_grams: 60,
      carbs_grams: 100,
      fat_grams: 30
    });
  }

  static createDinner(): NutritionLog {
    return this.createLog({
      source: 'Manual',
      calories: 700,
      protein_grams: 50,
      carbs_grams: 80,
      fat_grams: 25
    });
  }
}
