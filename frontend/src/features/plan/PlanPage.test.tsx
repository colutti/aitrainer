import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { usePlanStore } from '../../shared/hooks/usePlan';

import PlanPage from './PlanPage';

const mockNavigate = vi.fn();

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
    useNavigate: () => mockNavigate,
  };
});

describe('PlanPage', () => {
  const fetchPlan = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockReset();
    vi.mocked(usePlanStore).mockReturnValue({
      plan: null,
      isLoading: false,
      error: null,
      fetchPlan,
      setPlan: vi.fn(),
      clearPlan: vi.fn(),
      reset: vi.fn(),
    } as any);
  });

  it('loads plan on mount', async () => {
    render(<PlanPage />);

    await waitFor(() => {
      expect(fetchPlan).toHaveBeenCalledTimes(1);
    });
  });

  it('renders plan page title', () => {
    render(<PlanPage />);
    expect(screen.getByText('plan.title')).toBeInTheDocument();
  });

  it('opens chat with prefilled plan creation draft', () => {
    render(<PlanPage />);
    const button = screen.getByRole('button', { name: 'plan.empty.cta' });
    button.click();

    expect(mockNavigate).toHaveBeenCalledWith('/dashboard/chat', {
      state: { draftMessage: 'plan.empty.prefill_message' },
    });
  });
});
