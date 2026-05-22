export type PlanStatus = 'NO_PLAN' | 'DISCOVERY_IN_PROGRESS' | 'ACTIVE_PLAN';

export interface ProgressMetric {
  status: 'on_track' | 'off_track' | 'insufficient_data';
  details: string;
}

export interface PlanConflict {
  kind: string;
  message: string;
}

export interface PlanProgressSnapshot {
  plan_id: string;
  generated_at: string;
  training_adherence: ProgressMetric;
  nutrition_adherence: ProgressMetric;
  progression_status: 'progressing' | 'maintaining' | 'stalled' | 'regressing' | 'insufficient_data';
  body_trend_status: 'aligned' | 'misaligned' | 'insufficient_data';
  conflicts: PlanConflict[];
  recommended_review: boolean;
  evidence_summary: string[];
}

export interface DiscoveryView {
  missing_fields: string[];
  collected_fields: string[];
  next_prompt: string;
}

export interface NutritionTargetsView {
  calories_kcal: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g?: number;
}

export interface TodayTrainingView {
  day: string;
  routine_name?: string | null;
  focus: string;
  exercise_names: string[];
  is_rest_day: boolean;
}

export interface WeeklyScheduleView {
  day: string;
  routine_name?: string | null;
  focus: string;
  exercise_names: string[];
  is_rest_day: boolean;
  is_today: boolean;
}

export interface ActivePlanView {
  title: string;
  goal_summary: string;
  success_metrics: string[];
  training_split: string;
  weekly_schedule: WeeklyScheduleView[];
  today_training: TodayTrainingView;
  nutrition_targets: NutritionTargetsView;
  current_risks: string[];
  next_review_at?: string | null;
  latest_review_summary?: string | null;
}

export interface PlanViewModel {
  status: PlanStatus;
  generic_response_notice: string;
  discovery?: DiscoveryView | null;
  active_plan?: ActivePlanView | null;
  progress?: PlanProgressSnapshot | null;
}
