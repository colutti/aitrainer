import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useDashboardStore } from '../../shared/hooks/useDashboard';

import { DashboardPage } from './DashboardPage';

vi.mock('../../shared/hooks/useDashboard');

// Mock Chart components to avoid layout issues in JSDOM
vi.mock('./components/WidgetWeightChart', () => ({
  WidgetWeightChart: () => <div data-testid="weight-chart" />
}));
vi.mock('./components/WidgetRecentPRs', () => ({
  WidgetRecentPRs: () => <div data-testid="prs-widget" />
}));
vi.mock('./components/WidgetStrengthRadar', () => ({
  WidgetStrengthRadar: () => <div data-testid="radar-widget" />
}));
vi.mock('./components/WidgetVolumeTrend', () => ({
  WidgetVolumeTrend: () => <div data-testid="volume-widget" />
}));
vi.mock('./components/WidgetWeeklyFrequency', () => ({
  WidgetWeeklyFrequency: () => <div data-testid="frequency-widget" />
}));

describe('DashboardPage', () => {
  const mockFetchData = vi.fn();

  const defaultData = {
    stats: {
      metabolism: {
        tdee: 2500,
        daily_target: 2000,
        confidence: 'high',
        weekly_change: -0.5,
        energy_balance: -500,
        consistency_score: 95,
        macro_targets: { protein: 180, fat: 60, carbs: 200 },
        goal_type: 'lose',
      },
      body: { 
        weight_current: 80.0, 
        weight_diff: -1.2, 
        weight_trend: 'down',
        body_fat_pct: 15.0, 
        muscle_mass_pct: 42.0, 
        bmr: 1800 
      },
      calories: { consumed: 1500, target: 2000, percent: 75 },
      workouts: { completed: 3, target: 5 },
    },
    recentActivities: [
      { id: '1', type: 'workout', title: 'Treino A', subtitle: 'Peito', date: 'Hoje' },
      { id: '2', type: 'nutrition', title: 'Refeição', subtitle: 'Almoço', date: 'Hoje' },
      { id: '3', type: 'body', title: 'Pesagem', subtitle: '80kg', date: 'Hoje' },
    ],
    streak: { current_weeks: 5, current_days: 3 },
    weightHistory: [{ date: '2024-01-01', weight: 80 }],
    recentPRs: [{ id: '1', exercise: 'Squat', weight: 100, reps: 5, date: '2024-01-01' }],
    strengthRadar: { push: 0.8, pull: 0.7, legs: 0.9, core: 0.5 },
    volumeTrend: [1000, 1100],
    weeklyFrequency: [true, false, true, false, true, false, false],
  };

  const defaultHookValues = {
    data: null,
    isLoading: false,
    fetchData: mockFetchData,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useDashboardStore).mockReturnValue(defaultHookValues);
  });

  it('should render loading state when loading and no data', () => {
    vi.mocked(useDashboardStore).mockReturnValue({
      ...defaultHookValues,
      isLoading: true,
      data: null,
    });
    const { container } = render(<DashboardPage />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('should render dashboard content when data loaded', () => {
    vi.mocked(useDashboardStore).mockReturnValue({
      ...defaultHookValues,
      data: defaultData as any,
    });

    render(<DashboardPage />);

    expect(screen.getByText(/Bom dia/i)).toBeInTheDocument();
    expect(screen.getByText('2000')).toBeInTheDocument(); 
    expect(screen.getByText('2500')).toBeInTheDocument(); 
    expect(screen.getByText('95%')).toBeInTheDocument(); 
    expect(screen.getByText('80.0')).toBeInTheDocument();
    expect(screen.getByText('180g')).toBeInTheDocument(); 
    expect(screen.getByText('Treino A')).toBeInTheDocument();
    expect(screen.getByText('Refeição')).toBeInTheDocument();
    expect(screen.getByText('Pesagem')).toBeInTheDocument();
    
    // Widgets
    expect(screen.getByTestId('weight-chart')).toBeInTheDocument();
    expect(screen.getByTestId('prs-widget')).toBeInTheDocument();
    expect(screen.getByTestId('radar-widget')).toBeInTheDocument();
    expect(screen.getByTestId('volume-widget')).toBeInTheDocument();
    expect(screen.getByTestId('frequency-widget')).toBeInTheDocument();
  });

  it('should handle different metabolism confidence levels', () => {
    const confidenceLevels = ['high', 'medium', 'low', 'none'];
    confidenceLevels.forEach(level => {
      vi.mocked(useDashboardStore).mockReturnValue({
        ...defaultHookValues,
        data: {
          ...defaultData,
          stats: {
            ...defaultData.stats,
            metabolism: { ...defaultData.stats.metabolism, confidence: level }
          }
        } as any,
      });
      const { unmount } = render(<DashboardPage />);
      if (level === 'none') {
        expect(screen.getByText('TDEE: ---')).toBeInTheDocument();
      } else {
        const expected = { 'high': 'Alta', 'medium': 'Média', 'low': 'Baixa' }[level];
        expect(screen.getByText(`TDEE: ${expected}`)).toBeInTheDocument();
      }
      unmount();
    });
  });

  it('should handle missing widgets data', () => {
     vi.mocked(useDashboardStore).mockReturnValue({
      ...defaultHookValues,
      data: {
        ...defaultData,
        streak: null,
        recentPRs: null,
        strengthRadar: null,
        volumeTrend: null,
        weeklyFrequency: null,
      } as any,
    });

    render(<DashboardPage />);
    expect(screen.queryByTestId('prs-widget')).not.toBeInTheDocument();
    expect(screen.getByText('Dados de força insuficientes')).toBeInTheDocument();
  });

  it('should handle different weekly change directions', () => {
    // positive gain
    vi.mocked(useDashboardStore).mockReturnValue({
      ...defaultHookValues,
      data: {
        ...defaultData,
        stats: {
          ...defaultData.stats,
          metabolism: { ...defaultData.stats.metabolism, weekly_change: 0.5 }
        }
      } as any,
    });
    render(<DashboardPage />);
    expect(screen.getByText('0.50 kg')).toBeInTheDocument();
  });
});
