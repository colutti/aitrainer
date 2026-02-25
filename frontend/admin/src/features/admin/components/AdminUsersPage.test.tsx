import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useConfirmation } from '../../../../../src/shared/hooks/useConfirmation';
import { useNotificationStore } from '../../../../../src/shared/hooks/useNotification';
import { adminApi } from '../api/admin-api';

import { AdminUsersPage } from './AdminUsersPage';

vi.mock('../api/admin-api', () => ({
  adminApi: {
    listUsers: vi.fn(),
    deleteUser: vi.fn(),
    getUser: vi.fn(),
  },
}));

vi.mock('../../../../../src/shared/hooks/useConfirmation', () => ({
  useConfirmation: vi.fn(),
}));

vi.mock('../../../../../src/shared/hooks/useNotification', () => ({
  useNotificationStore: vi.fn(),
}));

describe('AdminUsersPage', () => {
  const mockNotify = { error: vi.fn(), success: vi.fn(), info: vi.fn() };
  const mockConfirm = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNotificationStore).mockReturnValue(mockNotify as any);
    vi.mocked(useConfirmation).mockReturnValue({ confirm: mockConfirm });
    // Ensure real timers
    vi.useRealTimers();
  });

  const mockUsers = [
    { email: 'user@test.com', name: 'User', is_admin: false, created_at: '2024-01-01T10:00:00Z' },
  ];

  it('should render and search users', async () => {
    vi.mocked(adminApi.listUsers).mockResolvedValue({ users: mockUsers, total: 1, page: 1, total_pages: 1, page_size: 20 });
    render(<AdminUsersPage />);
    
    // Initial fetch (500ms debounce)
    await waitFor(() => { expect(screen.getByText('user@test.com')).toBeInTheDocument(); }, { timeout: 3000 });

    const searchInput = screen.getByPlaceholderText(/Buscar por email/i);
    fireEvent.change(searchInput, { target: { value: 'test' } });
    
    // Search fetch (500ms debounce)
    await waitFor(() => { expect(adminApi.listUsers).toHaveBeenCalledWith(1, 20, 'test'); }, { timeout: 3000 });
  });

  it('should handle deletion success', async () => {
    vi.mocked(adminApi.listUsers).mockResolvedValue({ users: mockUsers, total: 1, page: 1, total_pages: 1, page_size: 20 });
    mockConfirm.mockResolvedValue(true);
    vi.mocked(adminApi.deleteUser).mockResolvedValue({ success: true });

    render(<AdminUsersPage />);
    
    await waitFor(() => { expect(screen.getByText('user@test.com')).toBeInTheDocument(); }, { timeout: 3000 });

    const deleteBtn = screen.getByTitle(/Deletar user@test.com/i);
    fireEvent.click(deleteBtn);

    expect(mockConfirm).toHaveBeenCalled();
    await waitFor(() => {
      expect(adminApi.deleteUser).toHaveBeenCalledWith('user@test.com');
      expect(mockNotify.success).toHaveBeenCalledWith('Usuário deletado com sucesso');
    }, { timeout: 3000 });
  });
});
