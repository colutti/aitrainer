export interface PlanOverview {
  id: string;
  title: string;
  primary_goal: string;
  objective_summary: string;
  success_criteria: string[];
  start_date: string;
  target_date: string;
  review_cadence: string;
  active_focus: string;
  last_updated_at: string;
}

export interface PlanStrategyView {
  rationale: string;
  adaptation_policy: string;
  constraints: string[];
  preferences: string[];
  current_risks: string[];
}

export interface PlanNutritionTargets {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g?: number;
}

export interface PlanRoutineExercise {
  name: string;
  sets: number;
  reps: string;
  load_guidance: string;
  rest_seconds?: number;
  tempo?: string;
  coach_notes?: string;
}

export interface PlanRoutine {
  id: string;
  name: string;
  objective?: string;
  warmup?: string;
  notes?: string;
  exercises: PlanRoutineExercise[];
}

export interface PlanWeeklyScheduleItem {
  day: string;
  routine_id?: string;
  focus: string;
  type: string;
}

export interface PlanCheckpoint {
  id: string;
  occurred_at: string;
  summary: string;
  decision: string;
  next_focus: string;
  evidence: string[];
}

export interface PlanTrainingProgram {
  split_name: string;
  frequency_per_week: number;
  session_duration_min: number;
  program_notes?: string;
  progression_rules: string[];
  review_triggers: string[];
  routines: PlanRoutine[];
  weekly_schedule: PlanWeeklyScheduleItem[];
}

export interface Plan {
  overview: PlanOverview;
  strategy: PlanStrategyView;
  nutrition_targets: PlanNutritionTargets;
  adherence_notes: string[];
  training_program: PlanTrainingProgram;
  latest_checkpoint: PlanCheckpoint | null;
}
