import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useConfirmation } from '../../../shared/hooks/useConfirmation';
import { adminApi } from '../api/admin-api';

import { AdminUsersPage } from './AdminUsersPage';

// Mock dependencies
vi.mock('../api/admin-api', () => ({
  adminApi: {
    listUsers: vi.fn(),
    getUserDetails: vi.fn(),
    deleteUser: vi.fn(),
  },
}));

vi.mock('../../../shared/hooks/useConfirmation', () => ({
  useConfirmation: vi.fn(),
}));

// Mock Notification Store
const mockNotify = {
  success: vi.fn(),
  error: vi.fn(),
  info: vi.fn(),
};

vi.mock('../../../shared/hooks/useNotification', () => ({
  useNotificationStore: () => mockNotify,
}));

describe('AdminUsersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useConfirmation as any).mockReturnValue({
      confirm: vi.fn().mockResolvedValue(true),
    });
  });

  const mockUsers = [
    { email: 'user@example.com', name: 'User', is_admin: false, created_at: '2024-01-01' },
    { email: 'admin@example.com', name: 'Admin', is_admin: true, created_at: '2024-01-01' },
  ];

  it('should render user list', async () => {
    vi.mocked(adminApi.listUsers).mockResolvedValue({
      users: mockUsers,
      total: 2,
      page: 1,
      page_size: 20,
      total_pages: 1,
    });

    render(<AdminUsersPage />);

    expect(await screen.findByText('user@example.com')).toBeInTheDocument();
    expect(screen.getByText('admin@example.com')).toBeInTheDocument();
  });

  it('should search users', async () => {
    const user = userEvent.setup();
    vi.mocked(adminApi.listUsers).mockResolvedValue({
      users: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    });

    render(<AdminUsersPage />);

    const searchInput = screen.getByPlaceholderText(/Buscar por email/i);
    await user.type(searchInput, 'test');

    await waitFor(() => {
      expect(adminApi.listUsers).toHaveBeenCalledWith(1, 20, 'test');
    }, { timeout: 1000 }); // Debounce might delay
  });

  it('should delete user after confirmation', async () => {
    vi.mocked(adminApi.listUsers).mockResolvedValue({
      users: [mockUsers[0]],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    });

    render(<AdminUsersPage />);
    
    // Wait for render
    expect(await screen.findByText('user@example.com')).toBeInTheDocument();

    // Click delete
    const deleteBtn = screen.getByLabelText('Deletar user@example.com');
    fireEvent.click(deleteBtn);

    await waitFor(() => {
      expect(adminApi.deleteUser).toHaveBeenCalledWith('user@example.com');
      expect(mockNotify.success).toHaveBeenCalled();
    });
  });

  it('should NOT allow deleting admin', async () => {
    vi.mocked(adminApi.listUsers).mockResolvedValue({
      users: [mockUsers[1]],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    });

    render(<AdminUsersPage />);

    expect(await screen.findByText('admin@example.com')).toBeInTheDocument();
    
    // Admin row should not have delete button or it should be disabled/hidden
    // Assuming UI renders a disabled button or tooltip
    const deleteBtn = screen.queryByLabelText('Deletar admin@example.com');
    // If we implement strictly, we might render a disabled button or different icon
    // For this test, let's assume we implement logic: if clicked on a potentially existing button (if any), it shouldn't trigger delete
    
    if (deleteBtn) {
        fireEvent.click(deleteBtn);
        expect(useConfirmation).not.toHaveBeenCalled(); // Shouldn't even ask confirm
        expect(adminApi.deleteUser).not.toHaveBeenCalled();
    }
  });
});
