import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { adminApi } from '../api/admin-api';

import { AdminLogsPage } from './AdminLogsPage';

vi.mock('../api/admin-api', () => ({
  adminApi: {
    getApplicationLogs: vi.fn(),
    getBetterStackLogs: vi.fn(),
  },
}));

describe('AdminLogsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render local logs by default', async () => {
    vi.mocked(adminApi.getApplicationLogs).mockResolvedValue({
      logs: ['[INFO] System started'],
      source: 'local',
      total: 1
    });

    render(<AdminLogsPage />);

    expect(await screen.findByText(/Logs do Sistema/i)).toBeInTheDocument();
    expect(await screen.findByText(/\[INFO\] System started/)).toBeInTheDocument();
  });

  it('should switch to BetterStack logs', async () => {
    vi.mocked(adminApi.getApplicationLogs).mockResolvedValue({
        logs: [], source: 'local', total: 0
    });
    vi.mocked(adminApi.getBetterStackLogs).mockResolvedValue({
      data: [{ message: 'BetterStack Log Entry' }],
      total: 1
    });

    render(<AdminLogsPage />);
    
    const betterStackBtn = screen.getByText(/BetterStack/i);
    fireEvent.click(betterStackBtn);

    await waitFor(() => {
      expect(adminApi.getBetterStackLogs).toHaveBeenCalled();
      expect(screen.getByText('BetterStack Log Entry')).toBeInTheDocument();
    });
  });

  it('should handle error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { /* no-op */ });
    vi.mocked(adminApi.getApplicationLogs).mockRejectedValue(new Error('Failed'));

    render(<AdminLogsPage />);

    expect(await screen.findByText(/Erro ao carregar logs/i)).toBeInTheDocument();
    
    consoleSpy.mockRestore();
  });
});
