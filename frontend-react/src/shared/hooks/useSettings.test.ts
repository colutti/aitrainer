import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../api/http-client';

import { useSettingsStore } from './useSettings';

// Mock httpClient
vi.mock('../api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('useSettingsStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useSettingsStore.getState().reset();
  });

  it('should have initial state', () => {
    const state = useSettingsStore.getState();
    expect(state.profile).toBeNull();
    expect(state.availableTrainers).toEqual([]);
    expect(state.isLoading).toBe(false);
  });

  it('should fetch profile successfully', async () => {
    const mockProfile = { email: 'test@example.com', age: 30 };
    vi.mocked(httpClient).mockResolvedValue(mockProfile);

    await useSettingsStore.getState().fetchProfile();

    const state = useSettingsStore.getState();
    expect(state.profile).toEqual(mockProfile);
    expect(httpClient).toHaveBeenCalledWith('/user/profile');
  });

  it('should update trainer successfully', async () => {
    const mockTrainer = { trainer_type: 'expert' };
    vi.mocked(httpClient).mockResolvedValue(mockTrainer);

    await useSettingsStore.getState().updateTrainer('expert');

    const state = useSettingsStore.getState();
    expect(state.trainer).toEqual(mockTrainer);
    expect(httpClient).toHaveBeenCalledWith('/trainer/profile', {
      method: 'POST',
      body: JSON.stringify({ trainer_type: 'expert' }),
    });
  });
});
