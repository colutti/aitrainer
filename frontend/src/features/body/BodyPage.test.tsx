import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';

import BodyPage from './BodyPage';

// Mocks
vi.mock('./components/WeightTab', () => ({
  WeightTab: () => <div data-testid="weight-tab">Weight Content</div>
}));

vi.mock('./components/NutritionTab', () => ({
  NutritionTab: () => <div data-testid="nutrition-tab">Nutrition Content</div>
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      if (key === 'body.weight_title') return 'Peso';
      if (key === 'body.nutrition_title') return 'Nutrição';
      return key;
    },
  }),
}));

describe('BodyPage', () => {
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
});
