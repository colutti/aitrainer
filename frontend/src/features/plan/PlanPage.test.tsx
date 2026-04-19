import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { usePlanStore } from '../../shared/hooks/usePlan';

import PlanPage from './PlanPage';

vi.mock('../../shared/hooks/usePlan', () => ({
  usePlanStore: vi.fn(),
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

describe('PlanPage', () => {
  const fetchActivePlan = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(usePlanStore).mockReturnValue({
      activePlan: null,
      isLoading: false,
      error: null,
      fetchActivePlan,
      setActivePlan: vi.fn(),
      clearActivePlan: vi.fn(),
      reset: vi.fn(),
    } as any);
  });

  it('loads active plan on mount', async () => {
    render(<PlanPage />);

    await waitFor(() => {
      expect(fetchActivePlan).toHaveBeenCalledTimes(1);
    });
  });

  it('renders plan page title', () => {
    render(<PlanPage />);
    expect(screen.getByText('plan.title')).toBeInTheDocument();
  });
});
