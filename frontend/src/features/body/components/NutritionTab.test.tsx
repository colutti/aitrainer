import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useNutritionStore } from '../../../shared/hooks/useNutrition';
import { render, screen, fireEvent } from '../../../shared/utils/test-utils';

import { NutritionTab } from './NutritionTab';

// Mocks
vi.mock('../../../shared/hooks/useNutrition');
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('NutritionTab', () => {
  const mockLogs = [
    { id: '1', date: '2024-01-01', calories: 2000, protein_grams: 150, carbs_grams: 200, fat_grams: 60, source: 'Manual' },
  ];

  const mockStats = {
    today: { calories: 1500, protein_grams: 100, carbs_grams: 150, fat_grams: 40 },
    daily_target: 2000,
    macro_targets: { protein: 150, carbs: 200, fat: 60 }
  };

  const defaultStore = {
    logs: [],
    stats: null,
    isLoading: false,
    error: null,
    page: 1,
    totalPages: 1,
    fetchLogs: vi.fn(),
    fetchStats: vi.fn(),
    deleteLog: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNutritionStore).mockReturnValue(defaultStore as any);
  });

  it('should call fetchLogs and fetchStats on mount', () => {
    render(<NutritionTab />);
    expect(defaultStore.fetchLogs).toHaveBeenCalled();
    expect(defaultStore.fetchStats).toHaveBeenCalled();
  });

  it('should render macro cards correctly', () => {
    vi.mocked(useNutritionStore).mockReturnValue({
      ...defaultStore,
      stats: mockStats,
    } as any);

    render(<NutritionTab />);
    expect(screen.getByText(/1500/)).toBeInTheDocument();
    expect(screen.getByText(/100/)).toBeInTheDocument();
  });

  it('should render logs list', () => {
    vi.mocked(useNutritionStore).mockReturnValue({
      ...defaultStore,
      logs: mockLogs,
      stats: mockStats,
    } as any);

    render(<NutritionTab />);
    // Check for the calorie value in the log card (2000 kcal). 
    // toLocaleString() in pt-BR might produce "2.000"
    expect(screen.getByText(/2.*000/)).toBeInTheDocument();
  });

  it('should navigate to chat when register meal clicked', () => {
    render(<NutritionTab />);
    const addBtn = screen.getByText(/Registrar Refeição/i);
    fireEvent.click(addBtn);
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard/chat');
  });
});
