import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { TrainerSettingsView } from './TrainerSettingsView';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

const mockTrainers = [
  { trainer_id: 'atlas', name: 'Atlas', short_description: 'Desc', catchphrase: 'Go!' },
  { trainer_id: 'gymbro', name: 'GymBro', short_description: 'Bro', catchphrase: 'Yo!' }
];

const mockProps = {
  availableTrainers: mockTrainers as any,
  selectedTrainerId: 'atlas',
  isSaving: false,
  isLoading: false,
  isFreePlan: true,
  onSelect: vi.fn(),
  onSave: vi.fn(),
  onRetry: vi.fn(),
};

describe('TrainerSettingsView', () => {
  it('renders trainer list correctly', () => {
    render(<TrainerSettingsView {...mockProps} />);
    expect(screen.getByText('Atlas')).toBeInTheDocument();
    expect(screen.getByText('GymBro')).toBeInTheDocument();
  });

  it('calls onSelect when a trainer card is clicked', () => {
    render(<TrainerSettingsView {...mockProps} />);
    const card = screen.getByTestId('trainer-card-gymbro');
    fireEvent.click(card);
    expect(mockProps.onSelect).toHaveBeenCalledWith('gymbro');
  });

  it('shows lock icon for premium trainers on free plan', () => {
    render(<TrainerSettingsView {...mockProps} isFreePlan={true} />);
    // Atlas is normally premium (logic in container, but view should render if lock prop true)
    // Actually, view should receive isLocked per trainer
    expect(screen.getAllByTestId('lock-icon').length).toBeGreaterThan(0);
  });

  it('calls onSave when save button is clicked', () => {
    render(<TrainerSettingsView {...mockProps} />);
    const saveBtn = screen.getByText('settings.trainer.save_button');
    fireEvent.click(saveBtn);
    expect(mockProps.onSave).toHaveBeenCalled();
  });
});
