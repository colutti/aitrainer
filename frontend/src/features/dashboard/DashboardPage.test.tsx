import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useAuthStore } from '../../shared/hooks/useAuth';
import { useDashboardStore } from '../../shared/hooks/useDashboard';
import { useNotificationStore } from '../../shared/hooks/useNotification';

import DashboardPage from './DashboardPage';

vi.mock('../../shared/hooks/useDashboard');
vi.mock('../../shared/hooks/useAuth');
vi.mock('../../shared/hooks/useNotification');
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'pt', changeLanguage: vi.fn() },
  }),
}));

// Mock Chart components to avoid layout issues in JSDOM
vi.mock('./components/WidgetWeightChart', () => ({
  WidgetWeightChart: () => <div data-testid="weight-chart" />
}));
vi.mock('./components/WidgetRecentPRs', () => ({
  WidgetRecentPRs: ({ prs }: any) => (
    <div data-testid="prs-widget">
      {(!prs || prs.length === 0) && 'Dados de força insuficientes'}
    </div>
  ),
}));
vi.mock('./components/WidgetStrengthRadar', () => ({
  WidgetStrengthRadar: () => <div data-testid="radar-widget" />
}));
vi.mock('./components/WidgetVolumeTrend', () => ({
  WidgetVolumeTrend: () => <div data-testid="volume-widget" />
}));
vi.mock('./components/WidgetWeeklyFrequency', () => ({
  WidgetWeeklyFrequency: ({ days }: any) => (
    <div data-testid="frequency-widget">
      {(!days || days.length === 0) && 'Nenhum treino esta semana'}
    </div>
  ),
}));

describe('DashboardPage', () => {
  const mockFetchData = vi.fn();
  const mockLoadUserInfo = vi.fn();
  const mockNotifySuccess = vi.fn();
  const mockNotifyInfo = vi.fn();

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
    weightTrend: [{ date: '2024-01-01', value: 80 }],
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
    vi.mocked(useAuthStore).mockReturnValue({
      userInfo: { name: 'Test User' },
      loadUserInfo: mockLoadUserInfo,
    } as any);
    vi.mocked(useNotificationStore).mockReturnValue({
      success: mockNotifySuccess,
      info: mockNotifyInfo,
    } as any);
  });

  it('should render loading state when loading and no data', () => {
    vi.mocked(useDashboardStore).mockReturnValue({
      ...defaultHookValues,
      isLoading: true,
      data: null,
    });
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );
    expect(screen.getByTestId('dashboard-skeleton')).toBeInTheDocument();
  });

  it('should render dashboard content when data loaded', () => {
    vi.mocked(useDashboardStore).mockReturnValue({
      ...defaultHookValues,
      data: defaultData as any,
    });

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    expect(screen.getByText('dashboard.greeting')).toBeInTheDocument();
    expect(screen.getByText('2000')).toBeInTheDocument(); 
    expect(screen.getByText('2500')).toBeInTheDocument(); 
    expect(screen.getByText(/75%/)).toBeInTheDocument(); 
    expect(screen.getByText(/80\.0/)).toBeInTheDocument();
    expect(screen.getByText('180g')).toBeInTheDocument(); 
    expect(screen.getByText('Treino A')).toBeInTheDocument();
    expect(screen.getByText('Refeição')).toBeInTheDocument();
    expect(screen.getByText('Pesagem')).toBeInTheDocument();

    // Widgets
    expect(screen.getByTestId('prs-widget')).toBeInTheDocument();
    expect(screen.getByTestId('radar-widget')).toBeInTheDocument();
    expect(screen.getByTestId('volume-widget')).toBeInTheDocument();
    expect(screen.getByTestId('frequency-widget')).toBeInTheDocument();
  });

  it('should handle different metabolism confidence levels', () => {
    const confidenceLevels = ['high', 'medium', 'low', null];
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
      const { unmount } = render(
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      );
      if (level === null) {
        expect(screen.getByText('dashboard.confidence_level.none')).toBeInTheDocument();
      } else {
        expect(screen.getByText(`dashboard.confidence_level.${level}`)).toBeInTheDocument();
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

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );
    expect(screen.getByTestId('prs-widget')).toBeInTheDocument(); // Widget renders with overlay
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
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );
    expect(screen.getByText((_content, element) => {
      const hasText = (node: Element) => node.textContent?.includes('0.50') && node.textContent?.includes('kg');
      const elementHasText = hasText(element!);
      const childrenDontHaveText = Array.from(element?.children ?? []).every(child => !hasText(child));
      return elementHasText && childrenDontHaveText;
    })).toBeInTheDocument();
  });

  it('should render Fat and Muscle diffs even if 7d is missing (sparse data)', () => {
    vi.mocked(useDashboardStore).mockReturnValue({
      ...defaultHookValues,
      data: {
        ...defaultData,
        stats: {
           ...defaultData.stats,
           body: {
             ...defaultData.stats.body,
             body_fat_pct: 15.0,
             fat_diff: null,
             fat_diff_15: -1.0,
             fat_diff_30: -2.0,
             muscle_mass_kg: 35.0,
             muscle_diff_kg: 0.5,
             muscle_diff_kg_15: 1.5,
           }
        }
      } as any,
    });

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    // Fat checks
    expect(screen.getAllByText(/15\.0/)[0]).toBeInTheDocument();

    // Muscle checks
    expect(screen.getAllByText(/35\.0/)[0]).toBeInTheDocument();
  });

  it('should trigger user info refresh and show success notification when payment is successful', () => {
    vi.mocked(useDashboardStore).mockReturnValue({
      ...defaultHookValues,
      data: defaultData as any,
    });

    render(
      <MemoryRouter initialEntries={['/dashboard?payment=success']}>
        <DashboardPage />
      </MemoryRouter>
    );

    expect(mockLoadUserInfo).toHaveBeenCalled();
    expect(mockNotifySuccess).toHaveBeenCalledWith(
      expect.stringContaining('landing.subscription.payment_success_message')
    );
  });

  it('should show info notification when payment is cancelled', () => {
    vi.mocked(useDashboardStore).mockReturnValue({
      ...defaultHookValues,
      data: defaultData as any,
    });

    render(
      <MemoryRouter initialEntries={['/dashboard?payment=cancelled']}>
        <DashboardPage />
      </MemoryRouter>
    );

    expect(mockNotifyInfo).toHaveBeenCalledWith(
      expect.stringContaining('landing.subscription.payment_cancelled_message')
    );
  });
});


