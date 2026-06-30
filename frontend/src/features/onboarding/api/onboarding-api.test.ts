import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../../../shared/api/http-client';

import { onboardingApi } from './onboarding-api';

vi.mock('../../../shared/api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('onboardingApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should validate token', async () => {
    const mockResponse = { valid: true, email: 'test@example.com' };
    vi.mocked(httpClient).mockResolvedValue(mockResponse);

    const result = await onboardingApi.validateToken('abc-123');
    expect(result).toEqual(mockResponse);
    expect(httpClient).toHaveBeenCalledWith('/onboarding/validate?token=abc-123');
  });

  it('should complete onboarding', async () => {
    const payload = {
      token: 'abc',
      password: 'SecurePass1',
      gender: 'Masculino',
      age: 30,
      weight: 80,
      height: 180,
      trainer_type: 'atlas',
      subscription_plan: 'Pro',
    };

    vi.mocked(httpClient).mockResolvedValue({ token: 'jwt-token' });

    await onboardingApi.completeOnboarding(payload);

    expect(httpClient).toHaveBeenCalledWith('/onboarding/complete', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  });

  it('should complete public onboarding', async () => {
    const payload = {
      gender: 'Feminino',
      age: 28,
      weight: 62,
      height: 168,
      trainer_type: 'sofia',
      subscription_plan: 'Pro',
      name: 'Public User',
    };

    vi.mocked(httpClient).mockResolvedValue({ token: 'jwt-token' });

    await onboardingApi.completePublicOnboarding(payload);

    expect(httpClient).toHaveBeenCalledWith('/onboarding/profile', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  });
});
