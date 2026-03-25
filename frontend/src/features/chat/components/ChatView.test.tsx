import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { ChatView } from './ChatView';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

const mockProps = {
  messages: [
    { id: '1', sender: 'Trainer' as const, text: 'Olá', timestamp: '2024-01-01T10:00:00Z' },
    { id: '2', sender: 'Student' as const, text: 'Oi', timestamp: '2024-01-01T10:01:00Z' }
  ],
  isStreaming: false,
  isLoading: false,
  hasMore: false,
  error: null,
  trainer: { trainer_id: 'atlas', name: 'Atlas' } as any,
  userInfo: { name: 'Student', photo_base64: 'base64' } as any,
  inputValue: '',
  setInputValue: vi.fn(),
  onSend: vi.fn(),
  onScroll: vi.fn(),
  scrollContainerRef: { current: null } as any,
  messagesEndRef: { current: null } as any,
  textareaRef: { current: null } as any,
};

describe('ChatView', () => {
  it('renders messages correctly', () => {
    render(<ChatView {...mockProps} />);
    expect(screen.getByText('Olá')).toBeInTheDocument();
    expect(screen.getByText('Oi')).toBeInTheDocument();
  });

  it('calls onSend when form is submitted', () => {
    const onSend = vi.fn();
    render(<ChatView {...mockProps} onSend={onSend} inputValue="Hello" />);
    const form = screen.getByTestId('chat-form');
    fireEvent.submit(form);
    expect(onSend).toHaveBeenCalled();
  });

  it('renders typing indicator when streaming', () => {
    render(<ChatView {...mockProps} isStreaming={true} />);
    expect(screen.getByText('chat.typing')).toBeInTheDocument();
  });

  it('renders limit error state correctly', () => {
    render(<ChatView {...mockProps} error="DAILY_LIMIT_REACHED" />);
    expect(screen.getByText('chat.daily_limit.title')).toBeInTheDocument();
  });
});
