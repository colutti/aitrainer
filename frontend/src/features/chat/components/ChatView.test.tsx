import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { afterEach, describe, it, expect, vi } from 'vitest';

import { ChatView } from './ChatView';

const i18n = {
  language: 'en-US',
};

afterEach(() => {
  i18n.language = 'en-US';
});

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n,
  }),
}));

const mockProps = {
  messages: [
    {
      id: '1',
      sender: 'Trainer' as const,
      text: 'Hello',
      translations: { 'pt-BR': 'Olá' },
      timestamp: '2024-01-01T10:00:00Z'
    },
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
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Oi')).toBeInTheDocument();
  });

  it('renders translated text for the selected locale', () => {
    i18n.language = 'pt-BR';

    render(<ChatView {...mockProps} />);

    expect(screen.getByText('Olá')).toBeInTheDocument();
    expect(screen.queryByText('Hello')).not.toBeInTheDocument();
  });

  it('updates the visible text when the locale changes', () => {
    const { rerender } = render(<ChatView {...mockProps} />);

    expect(screen.getByText('Hello')).toBeInTheDocument();

    i18n.language = 'pt-BR';
    rerender(<ChatView {...mockProps} />);

    expect(screen.getByText('Olá')).toBeInTheDocument();
    expect(screen.queryByText('Hello')).not.toBeInTheDocument();
  });

  it('calls onSend when form is submitted', () => {
    const onSend = vi.fn();
    render(<ChatView {...mockProps} onSend={onSend} inputValue="Hello" />);
    const form = screen.getByTestId('chat-form');
    fireEvent.submit(form);
    expect(onSend).toHaveBeenCalled();
  });

  it('allows selecting an image and submits with attachment payload', async () => {
    const onSend = vi.fn();
    render(<ChatView {...mockProps} onSend={onSend} />);

    class MockFileReader {
      result: string | ArrayBuffer | null = 'data:image/jpeg;base64,ZmFrZQ==';
      onload: null | (() => void) = null;
      onerror: null | (() => void) = null;
      readAsDataURL() {
        if (this.onload) this.onload();
      }
    }
    vi.stubGlobal('FileReader', MockFileReader as unknown as typeof FileReader);

    const file = new File(['fake'], 'photo.jpg', { type: 'image/jpeg' });
    const input = screen.getByTestId('chat-image-input');

    fireEvent.change(input, { target: { files: [file] } });
    await waitFor(() => {
      expect(screen.getByTestId('chat-image-clear-0')).toBeInTheDocument();
    });

    const form = screen.getByTestId('chat-form');
    fireEvent.submit(form);

    expect(onSend).toHaveBeenCalled();
    const callArg = onSend.mock.calls[0]?.[0];
    expect(callArg?.images?.length).toBe(1);
    expect(callArg?.images?.[0]?.mimeType).toBe('image/jpeg');
    expect(typeof callArg?.images?.[0]?.base64).toBe('string');

    vi.unstubAllGlobals();
  });

  it('renders typing indicator when streaming', () => {
    render(<ChatView {...mockProps} isStreaming={true} />);
    expect(screen.getByText('chat.typing')).toBeInTheDocument();
  });

  it('renders limit error state correctly', () => {
    render(<ChatView {...mockProps} error="DAILY_LIMIT_REACHED" />);
    expect(screen.getByText('chat.daily_limit.title')).toBeInTheDocument();
  });

  it('renders chat as read-only for demo users', () => {
    render(
      <ChatView
        {...mockProps}
        userInfo={{ ...mockProps.userInfo, is_demo: true }}
        inputValue="Should stay blocked"
      />
    );

    expect(screen.getByText('Demo read-only')).toBeInTheDocument();
    expect(screen.getByTestId('chat-input')).toBeDisabled();
  });
});
