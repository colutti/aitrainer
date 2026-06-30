import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

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
  isReadOnly: false,
  onSelect: vi.fn(),
  onSave: vi.fn(),
  onRetry: vi.fn(),
};

describe('TrainerSettingsView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

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
    expect(screen.getByTestId('trainer-card-atlas')).toContainElement(screen.getByTestId('lock-icon'));
    expect(screen.queryByTestId('trainer-card-gymbro')?.querySelector('[data-testid="lock-icon"]')).toBeNull();
  });

  it('calls onSave when save button is clicked', () => {
    render(<TrainerSettingsView {...mockProps} />);
    const saveBtn = screen.getByText('settings.trainer.save_button');
    fireEvent.click(saveBtn);
    expect(mockProps.onSave).toHaveBeenCalled();
  });

  it('disables trainer changes in read-only mode', () => {
    render(<TrainerSettingsView {...mockProps} isReadOnly />);
    expect(screen.getByTestId('trainer-card-gymbro')).toBeInTheDocument();
    expect(screen.getByText('settings.trainer.read_only')).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('trainer-card-gymbro'));
    expect(mockProps.onSelect).not.toHaveBeenCalled();
  });

  it('renders save button as disabled when no trainer is selected', () => {
    render(<TrainerSettingsView {...mockProps} selectedTrainerId="" />);
    expect(screen.getByRole('button', { name: 'settings.trainer.save_button' })).toBeDisabled();
  });

  it('shows loading indicator while saving', () => {
    render(<TrainerSettingsView {...mockProps} isSaving />);
    expect(screen.getByText('settings.trainer.saving')).toBeInTheDocument();
  });

  it('shows retry state when trainer catalog fails to load', () => {
    render(<TrainerSettingsView {...mockProps} availableTrainers={[]} />);
    fireEvent.click(screen.getByText('settings.trainer.retry'));
    expect(mockProps.onRetry).toHaveBeenCalled();
  });
});
