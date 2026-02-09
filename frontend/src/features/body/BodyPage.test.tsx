import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { BodyPage } from './BodyPage';
import { useMetabolismTab } from './hooks/useMetabolismTab';
import { useNutritionTab } from './hooks/useNutritionTab';
import { useWeightTab } from './hooks/useWeightTab';

// Mock the hooks
vi.mock('./hooks/useWeightTab');
vi.mock('./hooks/useNutritionTab');
vi.mock('./hooks/useMetabolismTab');

// Mock child components to verify which one is rendered
vi.mock('./components/WeightTab', () => ({
  WeightTab: () => <div data-testid="weight-tab">Weight Content</div>
}));
vi.mock('./components/NutritionTab', () => ({
  NutritionTab: () => <div data-testid="nutrition-tab">Nutrition Content</div>
}));

describe('BodyPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default mock returns
    vi.mocked(useWeightTab).mockReturnValue({
      stats: null,
      history: [],
      isLoading: false,
      isSaving: false,
      page: 1,
      totalPages: 1,
      register: vi.fn(),
      handleSubmit: vi.fn(),
      errors: {},
      deleteEntry: vi.fn(),
      editEntry: vi.fn(),
      changePage: vi.fn(),
      loadData: vi.fn()
    });
    
    vi.mocked(useNutritionTab).mockReturnValue({
      logs: [],
      stats: null,
      isLoading: false,
      isSaving: false,
      currentPage: 1,
      totalPages: 1,
      daysFilter: undefined,
      register: vi.fn(),
      handleSubmit: vi.fn(),
      errors: {},
      deleteEntry: vi.fn(),
      editEntry: vi.fn(),
      setFilter: vi.fn(),
      nextPage: vi.fn(),
      prevPage: vi.fn(),
      loadData: vi.fn(),
      changePage: vi.fn()
    });
    
    vi.mocked(useMetabolismTab).mockReturnValue({
      stats: null,
      isLoading: false,
      weeks: 3,
      loadData: vi.fn(),
      setWeeks: vi.fn()
    });
  });

  it('renders WeightTab by default (or when path does not include nutrition)', () => {
    render(
      <MemoryRouter initialEntries={['/body/weight']}>
        <Routes>
          <Route path="/body/*" element={<BodyPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Peso & Corpo')).toBeInTheDocument();
    expect(screen.getByTestId('weight-tab')).toBeInTheDocument();
  });

  it('renders NutritionTab when path includes nutrition', () => {
    render(
      <MemoryRouter initialEntries={['/body/nutrition']}>
        <BodyPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Dieta & Macros')).toBeInTheDocument();
    expect(screen.getByTestId('nutrition-tab')).toBeInTheDocument();
  });
});
