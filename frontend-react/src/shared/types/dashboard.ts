export interface DashboardStats {
  weight: {
    current: number;
    difference: number;
    trend: 'up' | 'down' | 'stable';
  };
  calories: {
    consumed: number;
    target: number;
    percent: number;
  };
  workouts: {
    completed: number;
    target: number;
    lastWorkoutDate?: string;
  };
  water: {
    consumed: number;
    target: number;
  };
}

export interface RecentActivity {
  id: string;
  type: 'workout' | 'nutrition' | 'body';
  title: string;
  subtitle: string;
  date: string;
  icon?: string;
}

export interface DashboardData {
  stats: DashboardStats;
  recentActivities: RecentActivity[];
}
