import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useBodyStore } from '../../../shared/hooks/useBody';
import { useConfirmation } from '../../../shared/hooks/useConfirmation';
import { useDemoMode } from '../../../shared/hooks/useDemoMode';
import type { WeightLog, WeightLogFormData } from '../../../shared/types/body';
import { render, screen, fireEvent, waitFor } from '../../../shared/utils/test-utils';

import { WeightTab } from './WeightTab';

vi.mock('../../../shared/hooks/useBody');
vi.mock('../../../shared/hooks/useConfirmation');
vi.mock('../../../shared/hooks/useDemoMode');

vi.mock('./WeightLogCard', () => ({
  WeightLogCard: ({ log, onDelete, onEdit, onClick }: any) => (
    <div data-testid={`weight-log-card-${log.id}`}>
      <button type="button" data-testid={`view-weight-${log.id}`} onClick={() => onClick(log)}>
        {log.weight_kg}
      </button>
      <button type="button" data-testid={`edit-weight-${log.id}`} onClick={() => onEdit(log)}>
        edit
      </button>
      <button type="button" data-testid={`delete-weight-${log.id}`} onClick={() => onDelete(log.date)}>
        delete
      </button>
    </div>
  ),
}));

vi.mock('./WeightLogDrawer', () => ({
  WeightLogDrawer: ({ isOpen, log, onSubmit, onClose }: any) => {
    if (!isOpen) return null;

    const payload: WeightLogFormData = log
      ? {
          date: '2026-04-02',
          weight_kg: 80.1,
          body_fat_pct: 14.2,
          muscle_mass_kg: 36.5,
          body_water_pct: 58.3,
          bone_mass_kg: 3.4,
          visceral_fat: 7,
          bmr: 1780,
          neck_cm: 38,
          chest_cm: 107,
          waist_cm: 84,
          hips_cm: 97,
          bicep_r_cm: 39,
          bicep_l_cm: 38.5,
          thigh_r_cm: 58,
          thigh_l_cm: 57.5,
          calf_r_cm: 39.2,
          calf_l_cm: 39.1,
          notes: 'updated weight note',
        }
      : {
          date: '2026-04-01',
          weight_kg: 79.4,
          body_fat_pct: 15.1,
          muscle_mass_kg: 36.1,
          body_water_pct: 57.8,
          bone_mass_kg: 3.3,
          visceral_fat: 8,
          bmr: 1765,
          neck_cm: 37.5,
          chest_cm: 106,
          waist_cm: 85,
          hips_cm: 98,
          bicep_r_cm: 38.2,
          bicep_l_cm: 38,
          thigh_r_cm: 57,
          thigh_l_cm: 56.5,
          calf_r_cm: 39,
          calf_l_cm: 38.8,
          notes: 'new weight note',
        };

    return (
      <div>
        <h2>{log ? 'Edit weight' : 'Create weight'}</h2>
        <button type="button" data-testid="submit-weight" onClick={() => void onSubmit(payload)}>
          submit
        </button>
        <button type="button" data-testid="close-weight" onClick={onClose}>
          close
        </button>
      </div>
    );
  },
}));

describe('WeightTab', () => {
  const mockLogs: WeightLog[] = [
    {
      id: 'weight-1',
      user_email: 'user@example.com',
      date: '2026-03-18',
      weight_kg: 79.2,
      body_fat_pct: 15.5,
      trend_weight: 79.4,
    },
  ];

  const defaultStore = {
    logs: [] as WeightLog[],
    isLoading: false,
    error: null,
    page: 1,
    totalPages: 1,
    fetchLogs: vi.fn(),
    fetchStats: vi.fn(),
    deleteLog: vi.fn(),
    logWeight: vi.fn(),
    updateWeight: vi.fn(),
  };

  const mockConfirm = vi.fn();
  const mockBlockIfReadOnly = vi.fn(() => false);

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useBodyStore).mockReturnValue(defaultStore as any);
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
    render(<WeightTab />);

    expect(defaultStore.fetchLogs).toHaveBeenCalledWith();
    expect(defaultStore.fetchStats).toHaveBeenCalledWith();
  });

  it('creates a weight log with all supported fields through the runtime component', async () => {
    render(<WeightTab />);

    fireEvent.click(screen.getByRole('button', { name: /Registrar Peso/i }));
    fireEvent.click(screen.getByTestId('submit-weight'));

    await waitFor(() => {
      expect(defaultStore.logWeight).toHaveBeenCalledWith({
        date: '2026-04-01',
        weight_kg: 79.4,
        body_fat_pct: 15.1,
        muscle_mass_kg: 36.1,
        body_water_pct: 57.8,
        bone_mass_kg: 3.3,
        visceral_fat: 8,
        bmr: 1765,
        neck_cm: 37.5,
        chest_cm: 106,
        waist_cm: 85,
        hips_cm: 98,
        bicep_r_cm: 38.2,
        bicep_l_cm: 38,
        thigh_r_cm: 57,
        thigh_l_cm: 56.5,
        calf_r_cm: 39,
        calf_l_cm: 38.8,
        notes: 'new weight note',
      });
    });
  });

  it('updates an existing weight log with all supported fields through the runtime component', async () => {
    vi.mocked(useBodyStore).mockReturnValue({
      ...defaultStore,
      logs: mockLogs,
    } as any);

    render(<WeightTab />);

    fireEvent.click(screen.getByTestId('edit-weight-weight-1'));
    fireEvent.click(screen.getByTestId('submit-weight'));

    await waitFor(() => {
      expect(defaultStore.updateWeight).toHaveBeenCalledWith('weight-1', {
        date: '2026-04-02',
        weight_kg: 80.1,
        body_fat_pct: 14.2,
        muscle_mass_kg: 36.5,
        body_water_pct: 58.3,
        bone_mass_kg: 3.4,
        visceral_fat: 7,
        bmr: 1780,
        neck_cm: 38,
        chest_cm: 107,
        waist_cm: 84,
        hips_cm: 97,
        bicep_r_cm: 39,
        bicep_l_cm: 38.5,
        thigh_r_cm: 58,
        thigh_l_cm: 57.5,
        calf_r_cm: 39.2,
        calf_l_cm: 39.1,
        notes: 'updated weight note',
      });
    });
  });

  it('confirms and deletes a weight log by date', async () => {
    vi.mocked(useBodyStore).mockReturnValue({
      ...defaultStore,
      logs: mockLogs,
    } as any);

    render(<WeightTab />);

    fireEvent.click(screen.getByTestId('delete-weight-weight-1'));

    await waitFor(() => {
      expect(mockConfirm).toHaveBeenCalled();
      expect(defaultStore.deleteLog).toHaveBeenCalledWith('2026-03-18');
    });
  });

  it('paginates through the runtime component', () => {
    vi.mocked(useBodyStore).mockReturnValue({
      ...defaultStore,
      logs: mockLogs,
      page: 2,
      totalPages: 3,
    } as any);

    render(<WeightTab />);

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
    vi.mocked(useBodyStore).mockReturnValue({
      ...defaultStore,
      logs: mockLogs,
    } as any);

    render(<WeightTab />);

    expect(screen.getByRole('button', { name: /Registrar Peso/i })).toBeDisabled();
    fireEvent.click(screen.getByTestId('edit-weight-weight-1'));
    fireEvent.click(screen.getByTestId('delete-weight-weight-1'));

    expect(readOnlyBlock).toHaveBeenCalledTimes(2);
    expect(defaultStore.logWeight).not.toHaveBeenCalled();
    expect(defaultStore.updateWeight).not.toHaveBeenCalled();
    expect(defaultStore.deleteLog).not.toHaveBeenCalled();
  });
});
