import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

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
    getDemoEpisode: vi.fn(),
    deleteDemoEpisode: vi.fn(),
    deleteDemoMessage: vi.fn(),
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
    vi.mocked(useNotificationStore).mockReturnValue(mockNotify as never);
    vi.mocked(useConfirmation).mockReturnValue({ confirm: mockConfirm });
    vi.useRealTimers();
  });

  it('should render and search users', async () => {
    vi.mocked(adminApi.listUsers).mockResolvedValue({
      users: [{ email: 'user@test.com', name: 'User', is_admin: false, created_at: '2024-01-01T10:00:00Z' }],
      total: 1,
      page: 1,
      total_pages: 1,
      page_size: 20,
    });

    render(<AdminUsersPage />);

    await waitFor(() => {
      expect(screen.getByText('user@test.com')).toBeInTheDocument();
    }, { timeout: 3000 });

    fireEvent.change(screen.getByPlaceholderText(/Buscar por email/i), {
      target: { value: 'test' },
    });

    await waitFor(() => {
      expect(adminApi.listUsers).toHaveBeenCalledWith(1, 20, 'test');
    }, { timeout: 3000 });
  });

  it('should handle deletion success', async () => {
    vi.mocked(adminApi.listUsers).mockResolvedValue({
      users: [{ email: 'user@test.com', name: 'User', is_admin: false, created_at: '2024-01-01T10:00:00Z' }],
      total: 1,
      page: 1,
      total_pages: 1,
      page_size: 20,
    });
    mockConfirm.mockResolvedValue(true);
    vi.mocked(adminApi.deleteUser).mockResolvedValue({ success: true });

    render(<AdminUsersPage />);

    await waitFor(() => {
      expect(screen.getByText('user@test.com')).toBeInTheDocument();
    }, { timeout: 3000 });

    fireEvent.click(screen.getByTitle(/Deletar user@test.com/i));

    expect(mockConfirm).toHaveBeenCalled();
    await waitFor(() => {
      expect(adminApi.deleteUser).toHaveBeenCalledWith('user@test.com');
      expect(mockNotify.success).toHaveBeenCalledWith('Usuário deletado com sucesso');
    }, { timeout: 3000 });
  });

  it('should display user plan and limits and allow updates', async () => {
    vi.mocked(adminApi.listUsers).mockResolvedValue({
      users: [{
        email: 'sub@test.com',
        name: 'Sub User',
        is_admin: false,
        created_at: '2024-01-01T10:00:00Z',
        subscription_plan: 'Pro',
        messages_sent_this_month: 250,
        custom_message_limit: null,
      }],
      total: 1,
      page: 1,
      total_pages: 1,
      page_size: 20,
    });
    vi.mocked(adminApi.getUser).mockResolvedValue({
      profile: {
        email: 'sub@test.com',
        is_admin: false,
        subscription_plan: 'Pro',
        messages_sent_this_month: 250,
        custom_message_limit: null,
      },
      stats: {},
    } as never);
    vi.mocked(adminApi.updateUser).mockResolvedValue({} as never);

    render(<AdminUsersPage />);

    await waitFor(() => {
      expect(screen.getByText('sub@test.com')).toBeInTheDocument();
    }, { timeout: 3000 });
    expect(screen.getAllByText('Pro').length).toBeGreaterThan(0);
    expect(screen.getByText('250 / 300')).toBeInTheDocument();

    fireEvent.click(screen.getByTitle(/Ver detalhes/i));

    await waitFor(() => {
      expect(screen.getByText('Editar Assinatura')).toBeInTheDocument();
    }, { timeout: 3000 });

    fireEvent.click(screen.getByText('Salvar Alterações'));
    await waitFor(() => {
      expect(adminApi.updateUser).toHaveBeenCalledWith('sub@test.com', expect.any(Object));
      expect(mockNotify.success).toHaveBeenCalledWith('Usuário atualizado com sucesso');
    });
  });

  it('should protect demo users from deletion and editing', async () => {
    vi.mocked(adminApi.listUsers).mockResolvedValue({
      users: [{ email: 'demo@fityq.it', name: 'Demo', is_admin: false, is_demo: true, created_at: '2024-01-01T10:00:00Z' }],
      total: 1,
      page: 1,
      total_pages: 1,
      page_size: 20,
    });
    vi.mocked(adminApi.getUser).mockResolvedValue({
      profile: {
        email: 'demo@fityq.it',
        is_admin: false,
        is_demo: true,
        subscription_plan: 'Free',
        custom_message_limit: null,
        custom_trial_days: null,
      },
      stats: {},
      demo_snapshot: {
        snapshot_id: 'snap-1',
        episode_count: 1,
        message_count: 2,
      },
      demo_episodes: [
        {
          episode_id: 'ep-1',
          title: 'Workout with gymbro',
          primary_domain: 'workout',
          trainers: ['gymbro'],
          started_at: '2026-03-01T10:00:00Z',
          ended_at: '2026-03-01T10:05:00Z',
          message_count: 2,
        },
      ],
    } as never);
    vi.mocked(adminApi.getDemoEpisode).mockResolvedValue({
      episode: {
        episode_id: 'ep-1',
        title: 'Workout with gymbro',
        primary_domain: 'workout',
        started_at: '2026-03-01T10:00:00Z',
        ended_at: '2026-03-01T10:05:00Z',
      },
      messages: [
        {
          message_id: 'msg-1',
          role: 'human',
          trainer_type: 'gymbro',
          timestamp: '2026-03-01T10:00:00Z',
          content: 'Treino feito',
        },
      ],
    } as never);
    vi.mocked(adminApi.deleteDemoMessage).mockResolvedValue({ message: 'ok' });

    render(<AdminUsersPage />);

    await waitFor(() => {
      expect(screen.getByText('demo@fityq.it')).toBeInTheDocument();
    }, { timeout: 3000 });
    expect(screen.getByText('DEMO')).toBeInTheDocument();
    expect(screen.queryByTitle(/Deletar demo@fityq.it/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByTitle(/Ver detalhes/i));

    await waitFor(() => {
      expect(screen.getByText(/Usuário demo protegido/i)).toBeInTheDocument();
    }, { timeout: 3000 });
    expect(screen.getByText('Salvar Alterações')).toBeDisabled();
    expect(screen.getByText('snap-1')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Ver'));
    await waitFor(() => {
      expect(screen.getByText('Treino feito')).toBeInTheDocument();
    }, { timeout: 3000 });

    const deleteButtons = screen.getAllByText('Excluir');
    expect(deleteButtons.length).toBeGreaterThan(1);
    fireEvent.click(deleteButtons[1]!);
    await waitFor(() => {
      expect(adminApi.deleteDemoMessage).toHaveBeenCalledWith('demo@fityq.it', 'msg-1');
    });
  });
});
