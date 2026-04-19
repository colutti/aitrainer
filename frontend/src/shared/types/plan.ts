export type PlanStatus =
  | 'draft'
  | 'awaiting_approval'
  | 'active'
  | 'adjustment_pending_approval'
  | 'completed'
  | 'archived';

export type PlanBannerTone = 'on_track' | 'attention' | 'pending_review' | 'awaiting_approval';

export type PlanUpcomingStatus = 'planned' | 'adjusted' | 'rest';

export interface PlanOverview {
  id: string;
  title: string;
  objective_summary: string;
  status: PlanStatus;
  start_date: string;
  end_date: string;
  progress_percent: number;
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

export interface PlanStatusBanner {
  tone: PlanBannerTone;
  message: string;
}

export interface Plan {
  overview: PlanOverview;
  mission_today: PlanMissionToday;
  upcoming_days: PlanUpcomingDay[];
  latest_checkpoint: PlanCheckpoint | null;
  status_banner: PlanStatusBanner;
}
