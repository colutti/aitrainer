import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { adminApi } from '../api/admin-api';

import { AdminDashboardPage } from './AdminDashboardPage';

// Mock adminApi
vi.mock('../api/admin-api', () => ({
  adminApi: {
    getOverview: vi.fn(),
    getQualityMetrics: vi.fn(),
  },
}));

describe('AdminDashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render detailed stats after loading', async () => {
    vi.mocked(adminApi.getOverview).mockResolvedValue({
      total_users: 100,
      total_admins: 2,
      active_users_7d: 50,
      active_users_24h: 10,
      total_messages: 5000,
      total_workouts: 200,
      total_nutrition_logs: 300,
    });

    vi.mocked(adminApi.getQualityMetrics).mockResolvedValue({
      avg_messages_per_user: 50,
      workout_engagement_rate: 75,
      nutrition_engagement_rate: 60,
    });

    render(<AdminDashboardPage />);

    // Check header - await it!
    expect(await screen.findByText('Admin Dashboard')).toBeInTheDocument();

    // Check values
    expect(screen.getByText('100')).toBeInTheDocument(); // total users
    expect(screen.getByText('5000')).toBeInTheDocument(); // total messages

    // Check quality metrics
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('should handle error state', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation((_msg) => { /* suppress error */ });
    vi.mocked(adminApi.getOverview).mockRejectedValue(new Error('Failed to fetch'));
    
    render(<AdminDashboardPage />);

    expect(await screen.findByText(/Erro ao carregar dados/i)).toBeInTheDocument();
    
    consoleSpy.mockRestore();
  });
});
