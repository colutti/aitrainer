import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../../../shared/api/http-client';

import { settingsApi } from './settings-api';

// Mock httpClient
vi.mock('../../../shared/api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('settingsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockProfile = { 
    email: 'test@test.com',
    gender: 'Masculino',
    age: 30,
    height: 180,
    notes: 'Sem restrições',
    display_name: 'Atleta Teste'
  };

  it('should get profile', async () => {
    vi.mocked(httpClient).mockResolvedValue(mockProfile);

    const result = await settingsApi.getProfile();

    expect(httpClient).toHaveBeenCalledWith('/user/profile');
    expect(result).toEqual(mockProfile);
  });

  it('should update profile', async () => {
    const updateData = { gender: 'Feminino', notes: 'Atualizado' };
    const mockResponse = { ...mockProfile, ...updateData };
    vi.mocked(httpClient).mockResolvedValue(mockResponse);

    const result = await settingsApi.updateProfile(updateData as any);

    expect(httpClient).toHaveBeenCalledWith('/user/update_profile', {
      method: 'POST',
      body: JSON.stringify(updateData),
    });
    expect(result).toEqual(mockResponse);
  });

  it('should get trainer profile', async () => {
    const mockTrainer = { trainer_type: 'expert' };
    vi.mocked(httpClient).mockResolvedValue(mockTrainer);

    const result = await settingsApi.getTrainer();

    expect(httpClient).toHaveBeenCalledWith('/trainer/trainer_profile');
    expect(result).toEqual(mockTrainer);
  });

  it('should update trainer profile', async () => {
    const trainerType = 'strict';
    const mockResponse = { trainer_type: 'strict' };
    vi.mocked(httpClient).mockResolvedValue(mockResponse);

    const result = await settingsApi.updateTrainer(trainerType);

    expect(httpClient).toHaveBeenCalledWith('/trainer/update_trainer_profile', {
      method: 'PUT',
      body: JSON.stringify({ trainer_type: trainerType }),
    });
    expect(result).toEqual(mockResponse);
  });

  it('should update identity fields', async () => {
    vi.mocked(httpClient).mockResolvedValue(undefined);

    await settingsApi.updateIdentity({
      display_name: 'Novo Nome',
      photo_base64: 'data:image/png;base64,abc123',
    });

    expect(httpClient).toHaveBeenCalledWith('/user/update_identity', {
      method: 'POST',
      body: JSON.stringify({
        display_name: 'Novo Nome',
        photo_base64: 'data:image/png;base64,abc123',
      }),
    });
  });
});
