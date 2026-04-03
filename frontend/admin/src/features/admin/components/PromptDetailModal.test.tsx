import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import type { PromptLog } from '../../../../../src/shared/types/admin';

import { PromptDetailModal } from './PromptDetailModal';

vi.mock('../../../../../src/shared/hooks/useNotification', () => ({
  useNotificationStore: () => ({ success: vi.fn(), error: vi.fn() }),
}));

describe('PromptDetailModal', () => {
  it('renders prompt format and raw calls metadata', async () => {
    const selectedPrompt: PromptLog = {
      id: '1',
      user_email: 'u@test.com',
      timestamp: '2026-04-03T10:00:00Z',
      model: 'gemini-1.5-flash',
      tokens_input: 100,
      tokens_output: 120,
      duration_ms: 420,
      status: 'success',
      prompt_format: 'markdown',
      raw_tools_called_count: 2,
      raw_tools_called: ['get_workouts_raw', 'get_nutrition_raw'],
      prompt: {
        prompt: '# FityQ AI\n\nPrompt',
        messages: [{ role: 'system', content: '# FityQ AI' }],
        tools: ['get_workouts_raw', 'get_nutrition_raw'],
      },
    };

    render(<PromptDetailModal selectedPrompt={selectedPrompt} onClose={() => {}} />);

    expect(screen.getByText(/markdown/i)).toBeInTheDocument();
    expect(screen.getByText(/raw calls: 2/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /Tools \(2\)/i }));
    expect(screen.getByText(/Raw Tools Called/i)).toBeInTheDocument();
  });
});
