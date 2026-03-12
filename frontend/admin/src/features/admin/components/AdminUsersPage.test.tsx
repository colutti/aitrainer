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
    updateUser: vi.fn(),
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

  it('should display user plan and limits and allow updates', async () => {
    const mockUsersSub = [
      { 
        email: 'sub@test.com', 
        name: 'Sub User', 
        is_admin: false, 
        created_at: '2024-01-01T10:00:00Z',
        subscription_plan: 'Pro',
        messages_sent_this_month: 250,
        custom_message_limit: null,
      },
    ];

    vi.mocked(adminApi.listUsers).mockResolvedValue({ users: mockUsersSub, total: 1, page: 1, total_pages: 1, page_size: 20 });
    vi.mocked(adminApi.getUser).mockResolvedValue({
      profile: {
        email: 'sub@test.com',
        is_admin: false,
        subscription_plan: 'Pro',
        messages_sent_this_month: 250,
        custom_message_limit: null,
      }
    } as any);
    
    vi.mocked(adminApi.updateUser).mockResolvedValue({} as any);

    render(<AdminUsersPage />);
    
    // Check if the user plan is rendered in the table correctly
    await waitFor(() => { expect(screen.getByText('sub@test.com')).toBeInTheDocument(); }, { timeout: 3000 });
    expect(screen.getAllByText('Pro').length).toBeGreaterThan(0);
    expect(screen.getByText('250 / 300')).toBeInTheDocument();

    // Open User Modal
    const viewBtn = screen.getByTitle(/Ver detalhes/i);
    fireEvent.click(viewBtn);

    await waitFor(() => { expect(screen.getByText('Editar Assinatura')).toBeInTheDocument(); }, { timeout: 3000 });
    expect(screen.getAllByText('Pro').length).toBeGreaterThan(0);

    // Allow user to interact with Custom Limit and Plan
    // There might not be an explicit accessible Role for the native select, try to find by DisplayValue if possible, or just click Save
    const saveBtn = screen.getByText('Salvar Alterações');
    expect(saveBtn).toBeInTheDocument();

    fireEvent.click(saveBtn);
    await waitFor(() => {
      expect(adminApi.updateUser).toHaveBeenCalledWith('sub@test.com', expect.any(Object));
      expect(mockNotify.success).toHaveBeenCalledWith('Usuário atualizado com sucesso');
    });
  });
});
