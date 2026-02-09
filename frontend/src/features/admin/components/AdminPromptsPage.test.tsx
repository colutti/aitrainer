import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useNotificationStore } from '../../../shared/hooks/useNotification';
import type { PromptLog, PromptListResponse } from '../../../shared/types/admin';
import { adminApi } from '../api/admin-api';

import { AdminPromptsPage } from './AdminPromptsPage';

vi.mock('../api/admin-api', () => ({
  adminApi: {
    listPrompts: vi.fn(),
    getPrompt: vi.fn(),
  },
}));

vi.mock('../../../shared/hooks/useNotification', () => ({
  useNotificationStore: vi.fn(),
}));

vi.mock('react-markdown', () => ({
  default: ({ children }: { children: string }) => <div data-testid="markdown">{children}</div>,
}));

describe('AdminPromptsPage', () => {
  const mockNotify = { error: vi.fn(), success: vi.fn(), info: vi.fn() };
  const mockClipboard = { writeText: vi.fn().mockResolvedValue(undefined) };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNotificationStore).mockReturnValue(mockNotify as any);
    vi.stubGlobal('navigator', { clipboard: mockClipboard });
    vi.useRealTimers();
  });

  const mockPrompts: PromptLog[] = [
    { 
      id: '1', 
      timestamp: '2024-01-01T10:00:00Z', 
      prompt_name: 'test-p', 
      user_email: 'u@test.com', 
      status: 'success',
      model: 'gpt-4',
      tokens_input: 10,
      tokens_output: 20,
      duration_ms: 100,
    },
  ];

  const mockListResponse: PromptListResponse = {
    prompts: mockPrompts,
    total: 1,
    page: 1,
    page_size: 20,
    total_pages: 1
  };

  it('should render and search prompts', async () => {
    vi.mocked(adminApi.listPrompts).mockResolvedValue(mockListResponse);
    render(<AdminPromptsPage />);
    
    await waitFor(() => { expect(screen.getByText('test-p')).toBeInTheDocument(); }, { timeout: 3000 });

    const searchInput = screen.getByPlaceholderText(/Filtrar por email/i);
    fireEvent.change(searchInput, { target: { value: 'test' } });
    
    await waitFor(() => { expect(adminApi.listPrompts).toHaveBeenCalledWith(1, 20, 'test'); }, { timeout: 3000 });
  });

  it('should handle prompt details and copy', async () => {
    vi.mocked(adminApi.listPrompts).mockResolvedValue(mockListResponse);
    vi.mocked(adminApi.getPrompt).mockResolvedValue({
      ...mockPrompts[0]!,
      prompt: { prompt: '# Hello' }
    });

    render(<AdminPromptsPage />);
    await waitFor(() => { expect(screen.getByText('test-p')).toBeInTheDocument(); }, { timeout: 3000 });

    const viewBtn = screen.getByTitle('Ver detalhes');
    fireEvent.click(viewBtn);

    expect(mockNotify.info).toHaveBeenCalledWith('Buscando detalhes do prompt...');
    
    await waitFor(() => {
      expect(screen.getByText(/Detalhes do Prompt/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    const copyBtn = screen.getByText(/Copiar JSON/i);
    fireEvent.click(copyBtn);
    expect(mockClipboard.writeText).toHaveBeenCalled();
  });
});
