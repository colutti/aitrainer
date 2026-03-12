import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../../../shared/api/http-client';

import { adminApi } from './admin-api';

vi.mock('../../../shared/api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('adminApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getOverview calls correct endpoint', async () => {
    vi.mocked(httpClient).mockResolvedValue({});
    await adminApi.getOverview();
    expect(httpClient).toHaveBeenCalledWith('/admin/analytics/overview');
  });

  it('getQualityMetrics calls correct endpoint', async () => {
    vi.mocked(httpClient).mockResolvedValue({});
    await adminApi.getQualityMetrics();
    expect(httpClient).toHaveBeenCalledWith('/admin/analytics/quality-metrics');
  });

  it('listUsers handles search param', async () => {
    vi.mocked(httpClient).mockResolvedValue({});
    await adminApi.listUsers(2, 50, 'joe');
    expect(httpClient).toHaveBeenCalledWith('/admin/users/?page=2&page_size=50&search=joe');
  });

  it('getUser calls correct endpoint', async () => {
    vi.mocked(httpClient).mockResolvedValue({});
    await adminApi.getUser('test@test.com');
    expect(httpClient).toHaveBeenCalledWith('/admin/users/test@test.com');
  });

  it('updateUser uses PATCH method', async () => {
    vi.mocked(httpClient).mockResolvedValue({});
    await adminApi.updateUser('joe@test.com', { name: 'Joe' });
    expect(httpClient).toHaveBeenCalledWith('/admin/users/joe@test.com', {
      method: 'PATCH',
      body: JSON.stringify({ name: 'Joe' }),
    });
  });

  it('deleteUser uses DELETE method', async () => {
    vi.mocked(httpClient).mockResolvedValue({});
    await adminApi.deleteUser('joe@test.com');
    expect(httpClient).toHaveBeenCalledWith('/admin/users/joe@test.com', {
      method: 'DELETE',
    });
  });


  it('listPrompts handles user_id param', async () => {
    vi.mocked(httpClient).mockResolvedValue({});
    await adminApi.listPrompts(1, 10, 'user123');
    expect(httpClient).toHaveBeenCalledWith('/admin/prompts/?page=1&page_size=10&user_id=user123');
  });

  it('getPrompt calls correct endpoint', async () => {
    vi.mocked(httpClient).mockResolvedValue({});
    await adminApi.getPrompt('prompt-123');
    expect(httpClient).toHaveBeenCalledWith('/admin/prompts/prompt-123');
  });
});
