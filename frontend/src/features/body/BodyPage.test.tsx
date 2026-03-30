import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useAuthStore } from '../../shared/hooks/useAuth';

import BodyPage from './BodyPage';

// Mocks
vi.mock('./components/WeightTab', () => ({
  WeightTab: () => <div data-testid="weight-tab">Weight Content</div>
}));

vi.mock('./components/NutritionTab', () => ({
  NutritionTab: () => <div data-testid="nutrition-tab">Nutrition Content</div>
}));

vi.mock('../../shared/hooks/useAuth', () => ({
  useAuthStore: vi.fn(),
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      if (key === 'body.weight_title') return 'Peso';
      if (key === 'body.nutrition_title') return 'Nutrição';
      if (key === 'body.weight_tab') return 'Peso';
      if (key === 'body.nutrition_tab') return 'Nutrição';
      return key;
    },
  }),
}));

describe('BodyPage', () => {
  beforeEach(() => {
    vi.mocked(useAuthStore).mockReturnValue({ userInfo: { is_demo: false } } as any);
  });

  it('renders WeightTab by default', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard/body/weight']}>
        <BodyPage />
      </MemoryRouter>
    );
    
    expect(screen.getByRole('heading', { name: /Peso/i })).toBeInTheDocument();
    expect(screen.getByTestId('weight-tab')).toBeInTheDocument();
  });

  it('renders NutritionTab when path includes nutrition', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard/body/nutrition']}>
        <BodyPage />
      </MemoryRouter>
    );
    
    expect(screen.getByRole('heading', { name: /Nutrição/i })).toBeInTheDocument();
    expect(screen.getByTestId('nutrition-tab')).toBeInTheDocument();
  });

  it('allows switching between body tabs', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard/body/weight']}>
        <BodyPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: /Nutrição/i }));

    expect(screen.getByRole('heading', { name: /Nutrição/i })).toBeInTheDocument();
    expect(screen.getByTestId('nutrition-tab')).toBeInTheDocument();
  });

  it('passes read-only mode to body tabs for demo users', () => {
    vi.mocked(useAuthStore).mockReturnValue({ userInfo: { is_demo: true } } as any);

    render(
      <MemoryRouter initialEntries={['/dashboard/body/weight']}>
        <BodyPage />
      </MemoryRouter>
    );

    expect(screen.getByTestId('weight-tab')).toBeInTheDocument();
  });
});
