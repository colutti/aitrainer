import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useMetabolismTab } from '../hooks/useMetabolismTab';

import { MetabolismTab } from './MetabolismTab';

// Mock hook
vi.mock('../hooks/useMetabolismTab');

// Mock Recharts
// Recharts uses ResizeObserver which is not in jsdom, and also canvas. 
// We mock the components to render simple divs.
vi.mock('recharts', async () => {
  const Original = await vi.importActual<unknown>('recharts');
  return {
    ...(Original as object),
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
    AreaChart: ({ children }: { children: React.ReactNode }) => <div data-testid="area-chart">{children}</div>,
    Area: () => <div data-testid="area" />,
    XAxis: () => <div data-testid="x-axis" />,
    YAxis: () => <div data-testid="y-axis" />,
    CartesianGrid: () => <div data-testid="cartesian-grid" />,
    Tooltip: () => <div data-testid="tooltip" />,
  };
});

describe('MetabolismTab', () => {
  const mockSetWeeks = vi.fn();
  const mockLoadData = vi.fn();

  const defaultHookValues = {
    stats: null,
    isLoading: false,
    weeks: 4,
    setWeeks: mockSetWeeks,
    loadData: mockLoadData,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useMetabolismTab).mockReturnValue(defaultHookValues as unknown as ReturnType<typeof useMetabolismTab>);
  });

  it('should render loading state', () => {
    vi.mocked(useMetabolismTab).mockReturnValue({
      ...defaultHookValues,
      isLoading: true,
    } as unknown as ReturnType<typeof useMetabolismTab>);

    const { container } = render(<MetabolismTab />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('should render stats and chart when data loaded', () => {
    const mockStats = {
      bmr: 1800,
      tdee: 2500,
      daily_target: 2000,
      goal_type: 'maintain',
      weekly_trend: [
        { week_start: '2024-01-01', avg_weight: 80, tdee: 2500 },
      ],
    };

    vi.mocked(useMetabolismTab).mockReturnValue({
      ...defaultHookValues,
      stats: mockStats,
    } as unknown as ReturnType<typeof useMetabolismTab>);

    render(<MetabolismTab />);
    
    // Check Stats Cards (updated to match component)
    expect(screen.getByText('TDEE Atual')).toBeInTheDocument();
    expect(screen.getByText('2500 kcal')).toBeInTheDocument();
    
    expect(screen.getByText('Meta Recomendada')).toBeInTheDocument();
    expect(screen.getByText('2000 kcal')).toBeInTheDocument();
  });

  it('should update weeks when range buttons clicked', () => {
     vi.mocked(useMetabolismTab).mockReturnValue({
      ...defaultHookValues,
      stats: {
         bmr: 0,
         tdee: 0,
         daily_target: 0,
         goal_type: 'maintain',
         weekly_trend: []
      } as unknown as ReturnType<typeof useMetabolismTab>['stats'],
    } as unknown as ReturnType<typeof useMetabolismTab>);

    render(<MetabolismTab />);
    
    const weeksBtn = screen.getByText('8 sem'); // "8 sem" from component
    fireEvent.click(weeksBtn);
    
    expect(mockSetWeeks).toHaveBeenCalledWith(8);
  });
});
