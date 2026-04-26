import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';

import BodyPage from './BodyPage';

vi.mock('./components/WeightTab', () => ({
  WeightTab: () => <div data-testid="weight-tab">Weight Content</div>
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      if (key === 'body.weight_title') return 'Peso';
      if (key === 'body.weight_subtitle') return 'Gerencie seu histórico';
      return key;
    },
  }),
}));

describe('BodyPage', () => {
  it('renders weight title and content without tabs', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard/body']}>
        <BodyPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: /Peso/i })).toBeInTheDocument();
    expect(screen.getByText(/Gerencie seu histórico/i)).toBeInTheDocument();
    expect(screen.getByTestId('weight-tab')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Nutrição/i })).not.toBeInTheDocument();
  });
});
