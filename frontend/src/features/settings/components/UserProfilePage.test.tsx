import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useDemoMode } from '../../../shared/hooks/useDemoMode';
import { render, screen, waitFor, fireEvent } from '../../../shared/utils/test-utils';
import { settingsApi } from '../api/settings-api';

import UserProfilePage from './UserProfilePage';

// Mocks
vi.mock('../api/settings-api');
vi.mock('../../../shared/hooks/useDemoMode', () => ({
  useDemoMode: vi.fn(),
}));
vi.mock('./UserProfileView', () => ({
  default: ({ profile, onSubmit, onPhotoUpload }: any) => (
    <div>
      <div data-testid="profile-form">{profile?.display_name ?? 'loading'}</div>
      <button
        type="button"
        data-testid="submit-changed-name"
        onClick={() =>
          void onSubmit({
            display_name: 'Jane Doe',
            gender: 'male',
            age: 34,
            height: 180,
          })
        }
      >
        submit changed
      </button>
      <button
        type="button"
        data-testid="submit-same-name"
        onClick={() =>
          void onSubmit({
            display_name: 'John Doe',
            gender: 'male',
            age: 31,
            height: 180,
          })
        }
      >
        submit same
      </button>
      <button
        type="button"
        data-testid="upload-photo"
        onClick={() =>
          void onPhotoUpload(new File(['avatar'], 'avatar.png', { type: 'image/png' }))
        }
      >
        upload photo
      </button>
    </div>
  ),
}));
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
    notes: 'Sem restrições',
    onboarding_completed: true,
    is_admin: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    class MockFileReader {
      public result: string | ArrayBuffer | null = null;
      public onloadend: null | (() => void) = null;

      readAsDataURL(_file: Blob) {
        this.result = 'data:image/png;base64,uploaded-avatar';
        this.onloadend?.();
      }
    }

    vi.stubGlobal('FileReader', MockFileReader as unknown as typeof FileReader);
    vi.mocked(useDemoMode).mockReturnValue({ isReadOnly: false } as any);
    vi.mocked(settingsApi.getProfile).mockResolvedValue(mockProfile as any);
    vi.mocked(settingsApi.updateProfile).mockResolvedValue({
      message: 'Profile updated successfully',
    } as any);
    vi.mocked(settingsApi.updateIdentity).mockResolvedValue(undefined);
  });

  it('should load and display profile data on mount', async () => {
    render(<UserProfilePage />);
    
    await waitFor(() => {
      expect(settingsApi.getProfile).toHaveBeenCalled();
      expect(screen.getByTestId('profile-form')).toHaveTextContent('John Doe');
    });
  });

  it('should handle profile update submission', async () => {
    vi.mocked(settingsApi.getProfile).mockResolvedValue(mockProfile as any);

    render(<UserProfilePage />);
    
    await waitFor(() => {
      expect(screen.getByTestId('profile-form')).toHaveTextContent('John Doe');
    });
    const initialLoadCalls = vi.mocked(settingsApi.getProfile).mock.calls.length;

    fireEvent.click(screen.getByTestId('submit-changed-name'));

    await waitFor(() => {
      expect(settingsApi.updateProfile).toHaveBeenCalledWith({
        display_name: 'Jane Doe',
        gender: 'male',
        age: 34,
        height: 180,
      });
    });

    await waitFor(() => {
      expect(settingsApi.updateIdentity).toHaveBeenCalledWith({
        display_name: 'Jane Doe',
      });
    });

    await waitFor(() => {
      expect(vi.mocked(settingsApi.getProfile).mock.calls.length).toBeGreaterThan(1);
    });
    expect(vi.mocked(settingsApi.getProfile).mock.calls.length).toBeGreaterThan(initialLoadCalls);
  });

  it('should not call updateIdentity when display name did not change', async () => {
    render(<UserProfilePage />);

    await waitFor(() => {
      expect(screen.getByTestId('profile-form')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('submit-same-name'));

    await waitFor(() => {
      expect(settingsApi.updateProfile).toHaveBeenCalledWith({
        display_name: 'John Doe',
        gender: 'male',
        age: 31,
        height: 180,
      });
    });

    expect(settingsApi.updateIdentity).not.toHaveBeenCalled();
  });

  it('should upload profile photo through updateIdentity and reload the profile', async () => {
    vi.mocked(settingsApi.getProfile)
      .mockResolvedValueOnce(mockProfile as any)
      .mockResolvedValueOnce({
        ...mockProfile,
        photo_base64: 'data:image/png;base64,uploaded-avatar',
      } as any);

    render(<UserProfilePage />);

    await waitFor(() => {
      expect(screen.getByTestId('profile-form')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('upload-photo'));

    await waitFor(() => {
      expect(settingsApi.updateIdentity).toHaveBeenCalledWith({
        photo_base64: 'data:image/png;base64,uploaded-avatar',
      });
    });

    await waitFor(() => {
      expect(vi.mocked(settingsApi.getProfile).mock.calls.length).toBeGreaterThan(1);
    });
  });

  it('reloads profile data even when identity update fails after basic profile save', async () => {
    vi.mocked(settingsApi.getProfile).mockResolvedValue(mockProfile as any);
    vi.mocked(settingsApi.updateIdentity).mockRejectedValueOnce(new Error('identity failed'));

    render(<UserProfilePage />);

    await waitFor(() => {
      expect(screen.getByTestId('profile-form')).toHaveTextContent('John Doe');
    });
    const initialLoadCalls = vi.mocked(settingsApi.getProfile).mock.calls.length;

    fireEvent.click(screen.getByTestId('submit-changed-name'));

    await waitFor(() => {
      expect(settingsApi.updateProfile).toHaveBeenCalledWith({
        display_name: 'Jane Doe',
        gender: 'male',
        age: 34,
        height: 180,
      });
    });

    await waitFor(() => {
      expect(settingsApi.updateIdentity).toHaveBeenCalledWith({
        display_name: 'Jane Doe',
      });
    });

    await waitFor(() => {
      expect(vi.mocked(settingsApi.getProfile).mock.calls.length).toBeGreaterThan(initialLoadCalls);
    });
  });
});
