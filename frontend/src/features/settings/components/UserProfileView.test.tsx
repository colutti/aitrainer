import { describe, it, expect, vi } from 'vitest';

import { render, screen, fireEvent, waitFor } from '../../../shared/utils/test-utils';

import UserProfileView from './UserProfileView';

describe('UserProfileView', () => {
  const mockProfile = {
    email: 'user@example.com',
    display_name: 'John Doe',
    gender: 'male',
    age: 30,
    height: 180,
    target_weight: 75,
    goal_type: 'lose' as const,
    weekly_rate: 0.5,
    onboarding_completed: true,
    is_admin: false,
    effective_remaining_messages: 50,
  };

  const mockProps = {
    profile: mockProfile,
    isLoading: false,
    isSaving: false,
    photoBase64: null,
    onSubmit: vi.fn().mockResolvedValue(undefined),
    onPhotoUpload: vi.fn().mockResolvedValue(undefined),
  };

  it('should render profile data correctly', () => {
    render(<UserProfileView {...mockProps} />);
    
    expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument();
    expect(screen.getByDisplayValue('30')).toBeInTheDocument();
    expect(screen.getByDisplayValue('180')).toBeInTheDocument();
    expect(screen.getByText('user@example.com')).toBeInTheDocument();
  });

  it('should call onSubmit with form data when save is clicked', async () => {
    render(<UserProfileView {...mockProps} />);
    
    const nameInput = screen.getByTestId('profile-name');
    fireEvent.change(nameInput, { target: { value: 'Jane Doe' } });
    
    fireEvent.submit(screen.getByTestId('profile-form'));
    
    await waitFor(() => {
      expect(mockProps.onSubmit).toHaveBeenCalled();
    });
  });

  it('should render loading skeleton when isLoading is true', () => {
    render(<UserProfileView {...mockProps} isLoading={true} />);
    
    expect(screen.queryByTestId('profile-form')).not.toBeInTheDocument();
    // Pulse animation class or specific skeleton markers
    const pulseElements = document.querySelectorAll('.animate-pulse');
    expect(pulseElements.length).toBeGreaterThan(0);
  });

  it('should submit when profile target_weight is null', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    render(
      <UserProfileView
        {...mockProps}
        profile={{ ...mockProfile, target_weight: null as unknown as number }}
        onSubmit={onSubmit}
      />
    );

    fireEvent.submit(screen.getByTestId('profile-form'));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalled();
    });
  });
});
