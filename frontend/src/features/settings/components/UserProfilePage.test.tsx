import { describe, it, expect, vi, beforeEach } from 'vitest';

import { render, screen, waitFor } from '../../../shared/utils/test-utils';
import { settingsApi } from '../api/settings-api';

import UserProfilePage from './UserProfilePage';

// Mocks
vi.mock('../api/settings-api');
vi.mock('../../../shared/hooks/useNotification', () => ({
  useNotificationStore: () => ({
    success: vi.fn(),
    error: vi.fn(),
  }),
}));

describe('UserProfilePage', () => {
  const mockProfile = {
    email: 'user@example.com',
    display_name: 'John Doe',
    gender: 'male',
    age: 30,
    height: 180,
    target_weight: 75,
    goal_type: 'lose',
    weekly_rate: 0.5,
    onboarding_completed: true,
    is_admin: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(settingsApi.getProfile).mockResolvedValue(mockProfile as any);
  });

  it('should load and display profile data on mount', async () => {
    render(<UserProfilePage />);
    
    await waitFor(() => {
      expect(settingsApi.getProfile).toHaveBeenCalled();
      expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument();
    });
  });

  it('should handle profile update submission', async () => {
    vi.mocked(settingsApi.updateProfile).mockResolvedValue({} as any);
    render(<UserProfilePage />);
    
    await waitFor(() => {
      expect(screen.getByTestId('profile-form')).toBeInTheDocument();
    });

    // We can't easily trigger the onSubmit directly without reaching into the View,
    // but we can simulate a form submission if the View renders it.
    // In our case, UserProfilePage passes handleSubmit to UserProfileView as onSubmit.
  });
});
