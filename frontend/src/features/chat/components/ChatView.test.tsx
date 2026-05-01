import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { afterEach, describe, it, expect, vi } from 'vitest';

import { ChatView } from './ChatView';

const i18n = {
  language: 'en-US',
};
const isDev = import.meta.env.DEV;

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
  debugTrace: null,
  debugTraceError: null,
  initialInputValue: '',
  onSend: vi.fn(),
  onScroll: vi.fn(),
  scrollContainerRef: { current: null } as any,
  messagesEndRef: { current: null } as any,
};

describe('ChatView', () => {
  it('renders workspace structure with the optional debug panel in dev', () => {
    render(<ChatView {...mockProps} />);
    expect(screen.getByTestId('chat-workspace')).toBeInTheDocument();
    expect(screen.getByTestId('chat-conversation-column')).toBeInTheDocument();
    if (isDev) {
      expect(screen.getByTestId('chat-context-panel')).toBeInTheDocument();
    } else {
      expect(screen.queryByTestId('chat-context-panel')).not.toBeInTheDocument();
    }
  });

  it('keeps chat form inside conversation column', () => {
    render(<ChatView {...mockProps} />);
    expect(screen.getByTestId('chat-conversation-column')).toContainElement(screen.getByTestId('chat-form'));
  });

  it('uses split layout when the debug panel is visible', () => {
    render(<ChatView {...mockProps} />);
    expect(screen.getByTestId('chat-workspace')).toHaveClass('lg:grid', 'lg:grid-cols-[minmax(0,1fr)_22rem]', 'lg:h-[calc(100dvh-7rem)]', 'lg:overflow-hidden');
  });

  it('keeps empty state rendering without context panel', () => {
    render(<ChatView {...mockProps} messages={[]} />);
    if (isDev) {
      expect(screen.getByTestId('chat-context-panel')).toBeInTheDocument();
    } else {
      expect(screen.queryByTestId('chat-context-panel')).not.toBeInTheDocument();
    }
    expect(screen.getByText('chat.start_conversation')).toBeInTheDocument();
  });

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
    render(<ChatView {...mockProps} onSend={onSend} initialInputValue="Hello" />);
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
    const imagesArg = onSend.mock.calls[0]?.[1];
    expect(imagesArg?.length).toBe(1);
    expect(imagesArg?.[0]?.mimeType).toBe('image/jpeg');
    expect(typeof imagesArg?.[0]?.base64).toBe('string');

    vi.unstubAllGlobals();
  });

  it('shows validation message when unsupported file format is selected', async () => {
    render(<ChatView {...mockProps} />);

    const file = new File(['fake'], 'photo.heic', { type: 'image/heic' });
    const input = screen.getByTestId('chat-image-input');
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByTestId('chat-upload-error')).toHaveTextContent(/formato de arquivo não suportado/i);
    });
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
          initialInputValue="Should stay blocked"
        />
      );

    expect(screen.getByText('Demo read-only')).toBeInTheDocument();
    expect(screen.getByTestId('chat-input')).toBeDisabled();
  });

  it('shows the last graph trace in the debug panel', () => {
    if (!isDev) return;

    render(
      <ChatView
        {...mockProps}
        debugTrace={{
          user_email: 'student@example.com',
          request_id: 'req-1',
          conversation_id: 'student@example.com',
          turn_id: 'turn-1',
          channel: 'app',
          status: 'success',
          error: null,
          started_at: '2026-05-01T10:00:00.000Z',
          ended_at: '2026-05-01T10:00:02.000Z',
          duration_ms: 2000,
          intent: 'training',
          security_status: 'safe',
          plan_needs_revision: false,
          tools_called: ['get_plan'],
          persistence_actions: [],
          final_response: 'Resposta final',
          technical_response: 'Resposta técnica',
          node_outputs: {
            turn_context: 'Contexto pronto',
          },
          nodes: [
            {
              node_name: 'turn_context',
              status: 'completed',
              started_at: '2026-05-01T10:00:00.000Z',
              completed_at: '2026-05-01T10:00:01.000Z',
              duration_ms: 1000,
              output_preview: 'Contexto pronto',
              error: null,
              config_hash: 'hash',
              config_version: 'v1',
              model: 'model',
            },
          ],
        }}
      />,
    );

    expect(screen.getByText('turn_context')).toBeInTheDocument();
    expect(screen.getByText('Contexto pronto')).toBeInTheDocument();
    expect(screen.getByText('Resposta final')).toBeInTheDocument();
  });
});
