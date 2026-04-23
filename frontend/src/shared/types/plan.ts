export type PlanUpcomingStatus = 'planned' | 'adjusted' | 'rest';

export interface PlanOverview {
  id: string;
  title: string;
  objective_summary: string;
  start_date: string;
  end_date: string;
  active_focus: string;
  last_updated_at: string;
}

export interface PlanMissionToday {
  training: string[];
  nutrition: string[];
  coaching: string;
}

export interface PlanUpcomingDay {
  date: string;
  label: string;
  training: string;
  training_details: string[];
  nutrition: string;
  status: PlanUpcomingStatus;
}

export interface PlanCheckpoint {
  id: string;
  occurred_at: string;
  summary: string;
  ai_assessment: string;
  decision: string;
  next_step: string;
}

export interface Plan {
  overview: PlanOverview;
  mission_today: PlanMissionToday;
  upcoming_days: PlanUpcomingDay[];
  latest_checkpoint: PlanCheckpoint | null;
}
