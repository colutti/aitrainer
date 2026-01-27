export interface NutritionLog {
  id: string;
  date: string;
  meal_name: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  notes?: string;
}

export interface NutritionStats {
  today: NutritionLog | null;
  weekly_adherence: boolean[];
  last_7_days: NutritionLog[];
  last_14_days: NutritionLog[];
  avg_daily_calories: number;
  avg_daily_calories_14_days: number;
  avg_protein: number;
  total_logs: number;
  macro_targets: { protein: number; carbs: number; fat: number };
  daily_target: number;
  stability_score: number;
  startDate: string;
  endDate: string;
  tdee: number | null;
  consistency_score: number | null;
  weight_logs_count: number | null;
}

export class NutritionFactory {
  static createLog(overrides?: Partial<NutritionLog>): NutritionLog {
    return {
      id: 'log_' + Date.now(),
      date: new Date().toISOString().split('T')[0],
      meal_name: 'Café da manhã',
      calories: 600,
      protein: 30,
      carbs: 80,
      fat: 20,
      ...overrides
    };
  }

  static createLogList(count: number, startDaysAgo: number = 0): NutritionLog[] {
    return Array.from({ length: count }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (startDaysAgo + i));
      return this.createLog({
        id: `log_${i}`,
        date: date.toISOString().split('T')[0],
        calories: 1800 + Math.random() * 400,
        protein: 120 + Math.random() * 30,
        carbs: 200 + Math.random() * 40,
        fat: 60 + Math.random() * 20
      });
    });
  }

  static createStats(overrides?: Partial<NutritionStats>): NutritionStats {
    return {
      today: this.createLog(),
      weekly_adherence: [true, false, true, true, false, true, true],
      last_7_days: this.createLogList(7),
      last_14_days: this.createLogList(14),
      avg_daily_calories: 2100,
      avg_daily_calories_14_days: 2050,
      avg_protein: 145,
      total_logs: 50,
      macro_targets: { protein: 150, carbs: 250, fat: 70 },
      daily_target: 2200,
      stability_score: 85,
      startDate: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      endDate: new Date().toISOString().split('T')[0],
      tdee: 2200,
      consistency_score: 88,
      weight_logs_count: 8,
      ...overrides
    };
  }

  static createBreakfast(): NutritionLog {
    return this.createLog({
      meal_name: 'Café da manhã',
      calories: 600,
      protein: 30,
      carbs: 80,
      fat: 20
    });
  }

  static createLunch(): NutritionLog {
    return this.createLog({
      meal_name: 'Almoço',
      calories: 850,
      protein: 60,
      carbs: 100,
      fat: 30
    });
  }

  static createDinner(): NutritionLog {
    return this.createLog({
      meal_name: 'Jantar',
      calories: 700,
      protein: 50,
      carbs: 80,
      fat: 25
    });
  }
}
