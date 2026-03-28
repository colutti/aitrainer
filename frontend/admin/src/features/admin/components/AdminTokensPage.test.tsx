import { useNotificationStore } from '@shared/hooks/useNotification';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { adminApi } from '../api/admin-api';

import { AdminTokensPage } from './AdminTokensPage';

const mockNotifications = {
  success: vi.fn(),
  error: vi.fn(),
  info: vi.fn(),
  show: vi.fn(),
  remove: vi.fn(),
  clear: vi.fn(),
  notifications: [],
};

vi.mock('@shared/hooks/useNotification', () => ({
  useNotificationStore: vi.fn(() => mockNotifications),
}));

vi.mock('../api/admin-api', () => ({
  adminApi: {
    getTokenSummary: vi.fn(),
    getTokenTimeseries: vi.fn(),
  },
}));

describe('AdminTokensPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNotificationStore).mockReturnValue(mockNotifications);
    vi.mocked(adminApi.getTokenSummary).mockResolvedValue({
      data: [
        {
          _id: 'user@test.com',
          total_input: 1000,
          total_output: 500,
          cost_usd: 1.25,
          message_count: 2,
          last_activity: '2026-03-27T10:00:00Z',
        },
      ],
    } as never);
    vi.mocked(adminApi.getTokenTimeseries).mockResolvedValue({
      data: [
        {
          date: '2026-03-27',
          tokens_input: 1000,
          tokens_output: 500,
        },
      ],
    } as never);
  });

  it('loads analytics, switches period, and refreshes', async () => {
    render(<AdminTokensPage />);

    await waitFor(() =>
      expect(screen.getByText('user@test.com')).toBeInTheDocument()
    );

    fireEvent.click(screen.getByRole('button', { name: '90d' }));
    await waitFor(() =>
      expect(adminApi.getTokenSummary).toHaveBeenCalledWith(90)
    );

    fireEvent.click(screen.getByRole('button', { name: 'Atualizar tokens' }));
    await waitFor(() => expect(adminApi.getTokenSummary).toHaveBeenCalledTimes(3));
  });
});
