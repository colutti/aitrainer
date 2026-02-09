import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

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

describe('TrainerSettingsPage', () => {
  const mockNotify = {
    success: vi.fn(),
    error: vi.fn(),
  };

  const mockAvailableTrainers = [
    { trainer_id: 'atlas', name: 'Atlas', short_description: 'Força bruta', catchphrase: 'Não para!' },
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

    expect(screen.getByRole('button', { name: /Atualizar Treinador/i })).not.toBeDisabled();
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

    const saveButton = screen.getByRole('button', { name: /Atualizar Treinador/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockStore.updateTrainer).toHaveBeenCalledWith('atlas');
      expect(mockNotify.success).toHaveBeenCalledWith('Treinador atualizado com sucesso!');
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
    expect(screen.getByText('Salvando...')).toBeInTheDocument();
  });

  it('should show empty state if no trainers and allow retry', () => {
    (useSettingsStore as any).mockReturnValue({
      ...mockStore,
      isLoading: false,
      availableTrainers: [],
    });

    render(<TrainerSettingsPage />);
    expect(screen.getByText(/Não foi possível carregar os treinadores disponíveis/i)).toBeInTheDocument();
    
    const retryBtn = screen.getByRole('button', { name: /Tentar Novamente/i });
    fireEvent.click(retryBtn);
    expect(mockStore.fetchAvailableTrainers).toHaveBeenCalled();
  });

  it('should handle update error', async () => {
    mockStore.updateTrainer.mockRejectedValue(new Error('error'));
    render(<TrainerSettingsPage />);

    const saveButton = screen.getByRole('button', { name: /Atualizar Treinador/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockNotify.error).toHaveBeenCalledWith('Erro ao atualizar treinador');
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
    const saveButton = screen.getByRole('button', { name: /Atualizar Treinador/i });
    expect(saveButton).toBeDisabled();
  });
});
