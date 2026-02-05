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

  it('should fetch overview', async () => {
    const mockOverview = { total_users: 10 };
    vi.mocked(httpClient).mockResolvedValue(mockOverview);

    const result = await adminApi.getOverview();
    expect(result).toEqual(mockOverview);
    expect(httpClient).toHaveBeenCalledWith('/admin/analytics/overview');
  });

  it('should fetch quality metrics', async () => {
    const mockMetrics = { avg_messages: 5 };
    vi.mocked(httpClient).mockResolvedValue(mockMetrics);

    const result = await adminApi.getQualityMetrics();
    expect(result).toEqual(mockMetrics);
    expect(httpClient).toHaveBeenCalledWith('/admin/analytics/quality-metrics');
  });

  it('should list users with pagination and search', async () => {
    const mockResponse = { users: [], total: 0 };
    vi.mocked(httpClient).mockResolvedValue(mockResponse);

    await adminApi.listUsers(2, 10, 'john');
    expect(httpClient).toHaveBeenCalledWith('/admin/users/list?page=2&page_size=10&search=john');
  });

  it('should get user details', async () => {
    const mockUser = { email: 'test@example.com' };
    vi.mocked(httpClient).mockResolvedValue(mockUser);

    await adminApi.getUserDetails('test@example.com');
    expect(httpClient).toHaveBeenCalledWith('/admin/users/test%40example.com/details');
  });

  it('should update user', async () => {
    const updates = { is_admin: true };
    await adminApi.updateUser('test@example.com', updates);
    expect(httpClient).toHaveBeenCalledWith('/admin/users/test%40example.com', {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  });

  it('should delete user', async () => {
    await adminApi.deleteUser('test@example.com');
    expect(httpClient).toHaveBeenCalledWith('/admin/users/test%40example.com', {
      method: 'DELETE',
    });
  });

  it('should get application logs', async () => {
    await adminApi.getApplicationLogs(50, 'ERROR');
    expect(httpClient).toHaveBeenCalledWith('/admin/logs/application?limit=50&level=ERROR');
  });

  it('should get betterstack logs', async () => {
    await adminApi.getBetterStackLogs(50, 'error');
    expect(httpClient).toHaveBeenCalledWith('/admin/logs/betterstack?limit=50&query=error');
  });

  it('should list prompts', async () => {
    await adminApi.listPrompts(1, 10, 'user@example.com');
    expect(httpClient).toHaveBeenCalledWith('/admin/prompts/list?page=1&page_size=10&user_email=user%40example.com');
  });
});
