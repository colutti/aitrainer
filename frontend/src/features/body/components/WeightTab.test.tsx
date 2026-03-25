import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useBodyStore } from '../../../shared/hooks/useBody';
import { render, screen, fireEvent } from '../../../shared/utils/test-utils';

import { WeightTab } from './WeightTab';

// Mocks
vi.mock('../../../shared/hooks/useBody');

describe('WeightTab', () => {
  const mockLogs = [
    { id: '1', date: '2024-01-01', weight_kg: 80, body_fat_pct: 15 },
    { id: '2', date: '2024-01-02', weight_kg: 81, body_fat_pct: 16 },
  ];

  const defaultStore = {
    logs: [],
    isLoading: false,
    error: null,
    fetchLogs: vi.fn(),
    fetchStats: vi.fn(),
    deleteLog: vi.fn(),
    logWeight: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useBodyStore).mockReturnValue(defaultStore as any);
  });

  it('should call fetchLogs on mount', () => {
    render(<WeightTab />);
    expect(defaultStore.fetchLogs).toHaveBeenCalled();
  });

  it('should render logs correctly', () => {
    vi.mocked(useBodyStore).mockReturnValue({
      ...defaultStore,
      logs: mockLogs,
    } as any);

    render(<WeightTab />);
    expect(screen.getByText(/80/)).toBeInTheDocument();
    expect(screen.getByText(/81/)).toBeInTheDocument();
  });

  it('should render empty state when no logs', () => {
    render(<WeightTab />);
    expect(screen.getByText(/Nenhum peso registrado/i)).toBeInTheDocument();
  });

  it('should open drawer when add button is clicked', () => {
    render(<WeightTab />);
    const addBtn = screen.getByText(/Registrar Peso/i);
    fireEvent.click(addBtn);
    expect(screen.getByRole('heading', { name: /Registrar Peso/i })).toBeInTheDocument();
  });
});
