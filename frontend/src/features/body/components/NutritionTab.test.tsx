import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useConfirmation } from '../../../shared/hooks/useConfirmation';
import { useDemoMode } from '../../../shared/hooks/useDemoMode';
import { useNutritionStore } from '../../../shared/hooks/useNutrition';
import type { NutritionLog, NutritionFormData } from '../../../shared/types/nutrition';
import { render, screen, fireEvent, waitFor } from '../../../shared/utils/test-utils';

import { NutritionTab } from './NutritionTab';

vi.mock('../../../shared/hooks/useNutrition');
vi.mock('../../../shared/hooks/useConfirmation');
vi.mock('../../../shared/hooks/useDemoMode');
vi.mock('../../nutrition/components/NutritionLogCard', () => ({
  NutritionLogCard: ({ log, onDelete, onEdit, onClick }: any) => (
    <div data-testid={`nutrition-log-card-${log.id}`}>
      <button type="button" data-testid={`view-nutrition-${log.id}`} onClick={() => onClick(log)}>
        {log.calories}
      </button>
      <button type="button" data-testid={`edit-nutrition-${log.id}`} onClick={() => onEdit(log)}>
        edit
      </button>
      <button type="button" data-testid={`delete-nutrition-${log.id}`} onClick={() => onDelete(log.id)}>
        delete
      </button>
    </div>
  ),
}));
vi.mock('./NutritionLogDrawer', () => ({
  NutritionLogDrawer: ({ isOpen, log, onSubmit, onClose }: any) => {
    if (!isOpen) return null;

    const payload: NutritionFormData = log
      ? {
          date: '2026-04-03',
          source: 'Manual',
          calories: 2350,
          protein_grams: 190,
          carbs_grams: 225,
          fat_grams: 75,
          fiber_grams: 31,
          sodium_mg: 1650,
        }
      : {
          date: '2026-04-02',
          source: 'Manual',
          calories: 2120,
          protein_grams: 180,
          carbs_grams: null,
          fat_grams: 68,
          fiber_grams: null,
          sodium_mg: null,
        };

    return (
      <div>
        <h2>{log ? 'Edit nutrition' : 'Create nutrition'}</h2>
        <button type="button" data-testid="submit-nutrition" onClick={() => void onSubmit(payload)}>
          submit
        </button>
        <button type="button" data-testid="close-nutrition" onClick={onClose}>
          close
        </button>
      </div>
    );
  },
}));

describe('NutritionTab', () => {
  const mockLogs: NutritionLog[] = [
    {
      id: 'nutrition-1',
      user_email: 'user@example.com',
      date: '2026-03-19',
      source: 'Manual',
      calories: 2100,
      protein_grams: 170,
      carbs_grams: 210,
      fat_grams: 70,
      fiber_grams: 28,
      sodium_mg: 1500,
    },
  ];

  const defaultStore = {
    logs: [] as NutritionLog[],
    stats: null,
    isLoading: false,
    error: null,
    page: 1,
    totalPages: 1,
    fetchLogs: vi.fn(),
    fetchStats: vi.fn(),
    deleteLog: vi.fn(),
    createLog: vi.fn(),
    updateLog: vi.fn(),
  };

  const mockConfirm = vi.fn();
  const mockBlockIfReadOnly = vi.fn(() => false);

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNutritionStore).mockReturnValue(defaultStore as any);
    vi.mocked(useConfirmation).mockReturnValue({ confirm: mockConfirm } as any);
    vi.mocked(useDemoMode).mockReturnValue({
      isReadOnly: false,
      isDemoUser: false,
      readOnlyMessage: 'Read-only mode',
      notifyReadOnly: vi.fn(),
      blockIfReadOnly: mockBlockIfReadOnly,
    } as any);
    mockConfirm.mockResolvedValue(true);
  });

  it('loads logs and stats on mount', () => {
    render(<NutritionTab />);

    expect(defaultStore.fetchLogs).toHaveBeenCalledWith();
    expect(defaultStore.fetchStats).toHaveBeenCalledWith();
  });

  it('creates a nutrition log through the runtime component and preserves cleared optional fields as null', async () => {
    render(<NutritionTab />);

    fireEvent.click(screen.getByRole('button', { name: /Registrar Refeição/i }));
    fireEvent.click(screen.getByTestId('submit-nutrition'));

    await waitFor(() => {
      expect(defaultStore.createLog).toHaveBeenCalledWith({
        date: '2026-04-02',
        source: 'Manual',
        calories: 2120,
        protein_grams: 180,
        carbs_grams: 0,
        fat_grams: 68,
        fiber_grams: null,
        sodium_mg: null,
      });
    });
  });

  it('updates an existing nutrition log through the runtime component', async () => {
    vi.mocked(useNutritionStore).mockReturnValue({
      ...defaultStore,
      logs: mockLogs,
    } as any);

    render(<NutritionTab />);

    fireEvent.click(screen.getByTestId('edit-nutrition-nutrition-1'));
    fireEvent.click(screen.getByTestId('submit-nutrition'));

    await waitFor(() => {
      expect(defaultStore.updateLog).toHaveBeenCalledWith('nutrition-1', {
        date: '2026-04-03',
        source: 'Manual',
        calories: 2350,
        protein_grams: 190,
        carbs_grams: 225,
        fat_grams: 75,
        fiber_grams: 31,
        sodium_mg: 1650,
      });
    });
  });

  it('confirms and deletes a nutrition log', async () => {
    vi.mocked(useNutritionStore).mockReturnValue({
      ...defaultStore,
      logs: mockLogs,
    } as any);

    render(<NutritionTab />);

    fireEvent.click(screen.getByTestId('delete-nutrition-nutrition-1'));

    await waitFor(() => {
      expect(mockConfirm).toHaveBeenCalled();
      expect(defaultStore.deleteLog).toHaveBeenCalledWith('nutrition-1');
    });
  });

  it('paginates through the runtime component', () => {
    vi.mocked(useNutritionStore).mockReturnValue({
      ...defaultStore,
      logs: mockLogs,
      page: 2,
      totalPages: 3,
    } as any);

    render(<NutritionTab />);

    fireEvent.click(screen.getByRole('button', { name: /Próxima/i }));
    fireEvent.click(screen.getByRole('button', { name: /Anterior/i }));

    expect(defaultStore.fetchLogs).toHaveBeenCalledWith(3);
    expect(defaultStore.fetchLogs).toHaveBeenCalledWith(1);
  });

  it('blocks create, edit and delete actions in read-only mode', async () => {
    const readOnlyBlock = vi.fn(() => true);
    vi.mocked(useDemoMode).mockReturnValue({
      isReadOnly: true,
      isDemoUser: true,
      readOnlyMessage: 'Read-only mode',
      notifyReadOnly: vi.fn(),
      blockIfReadOnly: readOnlyBlock,
    } as any);
    vi.mocked(useNutritionStore).mockReturnValue({
      ...defaultStore,
      logs: mockLogs,
    } as any);

    render(<NutritionTab />);

    expect(screen.getByRole('button', { name: /Registrar Refeição/i })).toBeDisabled();
    fireEvent.click(screen.getByTestId('edit-nutrition-nutrition-1'));
    fireEvent.click(screen.getByTestId('delete-nutrition-nutrition-1'));

    expect(readOnlyBlock).toHaveBeenCalledTimes(1);
    expect(defaultStore.createLog).not.toHaveBeenCalled();
    expect(defaultStore.updateLog).not.toHaveBeenCalled();
    expect(defaultStore.deleteLog).not.toHaveBeenCalled();
  });
});
