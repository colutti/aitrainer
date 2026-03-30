import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useAuthStore } from '../../shared/hooks/useAuth';
import { useConfirmation } from '../../shared/hooks/useConfirmation';
import { useNutritionStore } from '../../shared/hooks/useNutrition';

import NutritionPage from './NutritionPage';

// Mocks
vi.mock('../../shared/hooks/useNutrition', () => ({
  useNutritionStore: vi.fn(),
}));

vi.mock('../../shared/hooks/useAuth', () => ({
  useAuthStore: vi.fn(),
}));

vi.mock('../../shared/hooks/useConfirmation', () => ({
  useConfirmation: vi.fn(),
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      if (key === 'nutrition.weekly_days') return ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'];
      if (key === 'nutrition.title') return 'Nutrição';
      return key;
    },
  }),
}));

describe('NutritionPage', () => {
  const mockStore = {
    logs: [
      { id: '1', date: '2024-01-01', calories: 500, protein_grams: 30, carbs_grams: 50, fat_grams: 10, meal_type: 'Almoço' }
    ],
    stats: {
      today: { calories: 1500, protein_grams: 100, carbs_grams: 150, fat_grams: 40 },
      daily_target: 2500,
      macro_targets: { protein: 180, carbs: 250, fat: 80 },
      stability_score: 90,
      weekly_adherence: [true, true, true, false, true, false, false]
    },
    isLoading: false,
    fetchLogs: vi.fn(),
    fetchStats: vi.fn(),
    deleteLog: vi.fn(),
    page: 1,
    totalPages: 1,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNutritionStore).mockReturnValue(mockStore as any);
    vi.mocked(useConfirmation).mockReturnValue({ confirm: vi.fn().mockResolvedValue(true) } as any);
    vi.mocked(useAuthStore).mockReturnValue({ userInfo: { is_demo: false } } as any);
  });

  it('should render page title and progress cards', () => {
    render(
      <MemoryRouter>
        <NutritionPage />
      </MemoryRouter>
    );
    expect(screen.getByText(/Nutrição/i)).toBeInTheDocument();
    expect(screen.getByText(/1[.,]500/)).toBeInTheDocument(); 
    expect(screen.getByText(/100/)).toBeInTheDocument();  
    expect(mockStore.fetchLogs).toHaveBeenCalled();
    expect(mockStore.fetchStats).toHaveBeenCalled();
  });

  it('should handle log deletion with confirmation', async () => {
    render(
      <MemoryRouter>
        <NutritionPage />
      </MemoryRouter>
    );
    
    const deleteBtn = screen.getByLabelText(/Delete/i);
    fireEvent.click(deleteBtn);
    
    await waitFor(() => {
      expect(mockStore.deleteLog).toHaveBeenCalledWith('1');
    });
  });

  it('should show stability score and adherence', () => {
    render(
      <MemoryRouter>
        <NutritionPage />
      </MemoryRouter>
    );
    expect(screen.getByText(/90%/)).toBeInTheDocument();
  });

  it('should disable nutrition actions for demo users', () => {
    vi.mocked(useAuthStore).mockReturnValue({ userInfo: { is_demo: true } } as any);

    render(
      <MemoryRouter>
        <NutritionPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('button', { name: /nutrition\.register_meal/i })).toBeDisabled();
    expect(screen.queryByLabelText(/Delete/i)).not.toBeInTheDocument();
  });

  it('should render pagination when nutrition has multiple pages', () => {
    vi.mocked(useNutritionStore).mockReturnValue({
      ...mockStore,
      page: 2,
      totalPages: 4,
    } as any);

    render(
      <MemoryRouter>
        <NutritionPage />
      </MemoryRouter>
    );

    expect(screen.getByText((_content, element) => element?.textContent === '2 / 4')).toBeInTheDocument();
    expect(mockStore.fetchLogs).toHaveBeenCalled();
  });
});
