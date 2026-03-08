import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useAuthStore } from '../../../shared/hooks/useAuth';
import { useNotificationStore } from '../../../shared/hooks/useNotification';
import { useSettingsStore } from '../../../shared/hooks/useSettings';

import { TrainerSettingsPage } from './TrainerSettingsPage';

// Mock the hooks
vi.mock('../../../shared/hooks/useSettings', () => ({
  useSettingsStore: vi.fn(),
}));

vi.mock('../../../shared/hooks/useNotification', () => ({
  useNotificationStore: vi.fn(),
}));

vi.mock('../../../shared/hooks/useAuth', () => ({
  useAuthStore: vi.fn(),
}));

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe('TrainerSettingsPage', () => {
  const mockNotify = {
    success: vi.fn(),
    error: vi.fn(),
  };

  const mockAvailableTrainers = [
    { trainer_id: 'atlas', name: 'Atlas', short_description: 'Força bruta', catchphrase: 'Não para!' },
    { trainer_id: 'gymbro', name: 'Breno', short_description: 'Brother', catchphrase: 'Tamo junto!' },
    { trainer_id: 'luna', name: 'Luna', short_description: 'Zen', catchphrase: 'Respira.' },
    { trainer_id: 'unknown', name: 'Unknown', short_description: 'Test' }
  ];

  const mockTrainer = { trainer_type: 'atlas' };

  const mockStore = {
    trainer: mockTrainer,
    availableTrainers: mockAvailableTrainers,
    isLoading: false,
    isSaving: false,
    fetchTrainer: vi.fn(),
    fetchAvailableTrainers: vi.fn(),
    updateTrainer: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useNotificationStore as any).mockReturnValue(mockNotify);
    (useSettingsStore as any).mockReturnValue(mockStore);
    (useAuthStore as any).mockReturnValue({
      userInfo: { subscription_plan: 'Basic' }
    });
  });

  it('should render available trainers', async () => {
    render(<TrainerSettingsPage />);

    expect(screen.getByText('Atlas')).toBeInTheDocument();
    expect(screen.getByText('Luna')).toBeInTheDocument();
    expect(mockStore.fetchTrainer).toHaveBeenCalled();
    expect(mockStore.fetchAvailableTrainers).toHaveBeenCalled();
  });

  it('should select a trainer when clicked', async () => {
    render(<TrainerSettingsPage />);

    const lunaCard = screen.getByText('Luna').closest('div[class*="cursor-pointer"]');
    if (lunaCard) fireEvent.click(lunaCard);

    expect(screen.getByRole('button', { name: /settings.trainer.save_button/i })).not.toBeDisabled();
  });

  it('should handle image error and show fallback', () => {
    render(<TrainerSettingsPage />);
    const images = screen.getAllByRole('img');
    const atlasImg = images.find(img => img.getAttribute('alt') === 'Atlas');
    
    if (atlasImg) {
      fireEvent.error(atlasImg);
      expect(atlasImg).toHaveStyle({ display: 'none' });
      // Parent should have text 'A'
      expect(screen.getByText('A')).toBeInTheDocument();
    }
  });

  it('should update trainer successfully', async () => {
    mockStore.updateTrainer.mockResolvedValue({});
    render(<TrainerSettingsPage />);

    const saveButton = screen.getByRole('button', { name: /settings.trainer.save_button/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockStore.updateTrainer).toHaveBeenCalledWith('atlas');
      expect(mockNotify.success).toHaveBeenCalledWith('settings.trainer.update_success');
    });
  });

  it('should show loading state', () => {
    (useSettingsStore as any).mockReturnValue({
      ...mockStore,
      isLoading: true,
      availableTrainers: [],
    });

    render(<TrainerSettingsPage />);
    const skeletons = document.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('should show saving state', () => {
    (useSettingsStore as any).mockReturnValue({
        ...mockStore,
        isSaving: true
    });
    render(<TrainerSettingsPage />);
    expect(screen.getByText('settings.trainer.saving')).toBeInTheDocument();
  });

  it('should show empty state if no trainers and allow retry', () => {
    (useSettingsStore as any).mockReturnValue({
      ...mockStore,
      isLoading: false,
      availableTrainers: [],
    });

    render(<TrainerSettingsPage />);
    expect(screen.getByText(/settings.trainer.load_error/i)).toBeInTheDocument();
    
    const retryBtn = screen.getByRole('button', { name: /settings.trainer.retry/i });
    fireEvent.click(retryBtn);
    expect(mockStore.fetchAvailableTrainers).toHaveBeenCalled();
  });

  it('should handle update error', async () => {
    mockStore.updateTrainer.mockRejectedValue(new Error('error'));
    render(<TrainerSettingsPage />);

    const saveButton = screen.getByRole('button', { name: /settings.trainer.save_button/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockNotify.error).toHaveBeenCalledWith('settings.trainer.update_error');
    });
  });

  it('should return if no selected trainer (branch guard)', async () => {
    (useSettingsStore as any).mockReturnValue({
        ...mockStore,
        trainer: null
    });
    // Need to trigger handleSave without a selection
    // But since selectedTrainerId is initialized to empty if trainer is null, 
    // we need to make sure we don't select anything.
    render(<TrainerSettingsPage />);
    
    // If no selection, button should be disabled based on Component logic: disabled={isSaving || !selectedTrainerId}
    const saveButton = screen.getByRole('button', { name: /settings.trainer.save_button/i });
    expect(saveButton).toBeDisabled();
  });

  it('should lock non-gymbro trainers on Free plan', () => {
    (useAuthStore as any).mockReturnValue({
      userInfo: { subscription_plan: 'Free' }
    });

    render(<TrainerSettingsPage />);

    // Atlas should be locked
    const atlasText = screen.getByText('Atlas');
    // Find the container that has the border (which is the card)
    const atlasCard = atlasText.closest('div[class*="border-2"]');
    const lockIcons = screen.getAllByTestId('lock-icon');
    expect(atlasCard).toContainElement(lockIcons[0]!);
    
    // Clicking locked trainer should not update selection if we implement it that way
    // or we can just test that the lock icon is present.
  });
});

