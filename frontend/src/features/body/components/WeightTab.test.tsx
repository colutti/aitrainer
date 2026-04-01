import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useAuthStore } from '../../../shared/hooks/useAuth';
import { useBodyStore } from '../../../shared/hooks/useBody';
import { render, screen, fireEvent } from '../../../shared/utils/test-utils';

import { WeightTab } from './WeightTab';

// Mocks
vi.mock('../../../shared/hooks/useBody');
vi.mock('../../../shared/hooks/useAuth', () => ({
  useAuthStore: vi.fn(),
}));

describe('WeightTab', () => {
  const mockLogs = [
    { id: '1', date: '2024-01-01', weight_kg: 80, body_fat_pct: 15 },
    { id: '2', date: '2024-01-02', weight_kg: 81, body_fat_pct: 16 },
  ];

  const defaultStore = {
    logs: [],
    isLoading: false,
    error: null,
    page: 1,
    totalPages: 1,
    fetchLogs: vi.fn(),
    fetchStats: vi.fn(),
    deleteLog: vi.fn(),
    logWeight: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useBodyStore).mockReturnValue(defaultStore as any);
    vi.mocked(useAuthStore).mockReturnValue({ userInfo: { is_demo: false } } as any);
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
    const addBtn = screen.getByRole('button', { name: /Registrar Peso/i });
    expect(addBtn.className).toContain('w-full');
    fireEvent.click(addBtn);
    expect(screen.getByRole('heading', { name: /Registrar Peso/i })).toBeInTheDocument();
  });

  it('should disable weight actions for demo users', () => {
    vi.mocked(useAuthStore).mockReturnValue({ userInfo: { is_demo: true } } as any);

    render(<WeightTab />);

    expect(screen.getByRole('button', { name: /Registrar Peso/i })).toBeDisabled();
    expect(screen.queryByTestId('btn-delete-weight')).not.toBeInTheDocument();
  });

  it('should allow viewing a weight log in demo mode', () => {
    vi.mocked(useAuthStore).mockReturnValue({ userInfo: { is_demo: true } } as any);
    vi.mocked(useBodyStore).mockReturnValue({
      ...defaultStore,
      logs: mockLogs,
    } as any);

    render(<WeightTab />);

    fireEvent.click(screen.getAllByTestId('weight-log-card')[0]!);

    expect(screen.getByRole('heading', { name: /Detalhes do Registro|Record Details/i })).toBeInTheDocument();
    expect(screen.getByText('80.0')).toBeInTheDocument();
  });

  it('should render pagination when there are multiple pages', () => {
    vi.mocked(useBodyStore).mockReturnValue({
      ...defaultStore,
      totalPages: 3,
      page: 2,
      logs: mockLogs,
    } as any);

    render(<WeightTab />);

    expect(screen.getByText(/2\s*\/\s*3/)).toBeInTheDocument();
    expect(screen.getAllByRole('button').length).toBeGreaterThan(3);
  });
});
