import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { adminApi, PromptLog } from '../api/admin-api';

import { AdminPromptsPage } from './AdminPromptsPage';

vi.mock('../api/admin-api', () => ({
  adminApi: {
    listPrompts: vi.fn(),
  },
}));

// Mock Notification
const mockNotify = {
  success: vi.fn(),
  info: vi.fn(),
  error: vi.fn(),
};

vi.mock('../../../shared/hooks/useNotification', () => ({
  useNotificationStore: () => mockNotify,
}));

describe('AdminPromptsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockPrompts: PromptLog[] = [
    {
      id: '1',
      user_email: 'user@example.com',
      timestamp: '2024-01-01',
      model: 'gpt-4',
      tokens_input: 100,
      tokens_output: 50,
      duration_ms: 500,
      status: 'success',
      prompt_name: 'test_prompt'
    }
  ];

  it('should render prompts list', async () => {
    vi.mocked(adminApi.listPrompts).mockResolvedValue({
      prompts: mockPrompts,
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1
    });

    render(<AdminPromptsPage />);
    
    expect(await screen.findByText('test_prompt')).toBeInTheDocument();
    expect(screen.getByText('user@example.com')).toBeInTheDocument();
    expect(screen.getByText('gpt-4')).toBeInTheDocument();
  });

  it('should show details on click', async () => {
    vi.mocked(adminApi.listPrompts).mockResolvedValue({
        prompts: mockPrompts,
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1
    });

    render(<AdminPromptsPage />);
    
    await screen.findByText('test_prompt');
    
    // View details button
    const viewBtns = screen.getAllByRole('button', { name: /ver detalhes/i });
    fireEvent.click(viewBtns[0]);

    // Should show modal with details
    expect(await screen.findByText('Detalhes do Prompt')).toBeInTheDocument();
    // Verify JSON content is present (simple check)
    expect(screen.getByText(/"id": "1"/)).toBeInTheDocument();
  });
});
