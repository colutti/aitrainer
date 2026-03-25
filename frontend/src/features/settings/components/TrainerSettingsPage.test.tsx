import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useAuthStore } from '../../../shared/hooks/useAuth';
import { useSettingsStore } from '../../../shared/hooks/useSettings';

import TrainerSettingsPage from './TrainerSettingsPage';

// Mocks
vi.mock('../../../shared/hooks/useAuth', () => ({
  useAuthStore: vi.fn(),
}));

vi.mock('../../../shared/hooks/useSettings', () => ({
  useSettingsStore: vi.fn(),
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      if (key.includes('gymbro')) return 'GymBro';
      if (key.includes('atlas')) return 'Atlas';
      return key;
    },
  }),
}));

describe('TrainerSettingsPage', () => {
  const mockFetchTrainer = vi.fn();
  const mockFetchAvailableTrainers = vi.fn();
  const mockUpdateTrainer = vi.fn();

  const defaultStoreValues = {
    trainer: { trainer_type: 'atlas' },
    availableTrainers: [
      { trainer_id: 'atlas', name: 'Atlas', short_description: 'Pro', catchphrase: 'Go' },
      { trainer_id: 'gymbro', name: 'GymBro', short_description: 'Bro', catchphrase: 'Yo' },
    ],
    isLoading: false,
    isSaving: false,
    fetchTrainer: mockFetchTrainer,
    fetchAvailableTrainers: mockFetchAvailableTrainers,
    updateTrainer: mockUpdateTrainer,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useSettingsStore).mockReturnValue(defaultStoreValues as any);
    vi.mocked(useAuthStore).mockReturnValue({
      userInfo: { subscription_plan: 'Pro' }
    } as any);
  });

  it('should render trainers and highlight current one', async () => {
    render(<TrainerSettingsPage />);
    
    await waitFor(() => {
      expect(screen.getAllByText(/Atlas/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/GymBro/i).length).toBeGreaterThan(0);
    });
  });

  it('should allow selecting and saving a trainer', async () => {
    render(<TrainerSettingsPage />);
    
    await waitFor(() => expect(screen.getAllByText(/GymBro/i).length).toBeGreaterThan(0));
    
    const gymbroCard = screen.getByTestId('trainer-card-gymbro');
    fireEvent.click(gymbroCard);
    
    const saveBtn = screen.getByText(/settings\.trainer\.save_button/i);
    fireEvent.click(saveBtn);
    
    await waitFor(() => {
      expect(mockUpdateTrainer).toHaveBeenCalledWith('gymbro');
    });
  });

  it('should lock non-gymbro trainers on Free plan', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      userInfo: { subscription_plan: 'Free' }
    } as any);

    render(<TrainerSettingsPage />);
    
    await waitFor(() => {
      const atlasCard = screen.getByTestId('trainer-card-atlas');
      expect(atlasCard).toContainElement(screen.getByTestId('lock-icon'));
    });
  });
});
