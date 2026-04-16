import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useChatStore } from '../../shared/hooks/useChat';
import { useSettingsStore } from '../../shared/hooks/useSettings';

import ChatPage from './ChatPage';

vi.mock('../../shared/hooks/useChat');
vi.mock('../../shared/hooks/useSettings');

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

describe('ChatPage', () => {
  const mockSendMessage = vi.fn();
  const mockFetchHistory = vi.fn();
  const mockFetchTrainer = vi.fn();
  const mockFetchAvailable = vi.fn();

  const defaultChatStore = {
    messages: [],
    isStreaming: false,
    error: null,
    fetchHistory: mockFetchHistory,
    sendMessage: mockSendMessage,
  };

  const defaultSettingsStore = {
    trainer: { trainer_type: 'marcus' },
    availableTrainers: [
      { trainer_id: 'marcus', name: 'Marcus', specialty: 'Strength' },
    ],
    fetchTrainer: mockFetchTrainer,
    fetchAvailableTrainers: mockFetchAvailable,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useChatStore).mockReturnValue(defaultChatStore);
    vi.mocked(useSettingsStore).mockReturnValue(defaultSettingsStore);
  });

  it('should render empty state when no messages', () => {
    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>
    );
    expect(screen.getByText(/Começar conversa/i)).toBeInTheDocument();
  });

  it('should fetch trainer and available trainers if empty', () => {
    vi.mocked(useSettingsStore).mockReturnValue({
        ...defaultSettingsStore,
        availableTrainers: []
    });
    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>
    );
    expect(mockFetchTrainer).toHaveBeenCalled();
    expect(mockFetchAvailable).toHaveBeenCalled();
  });

  it('should render default trainer name when trainer not found', () => {
    vi.mocked(useSettingsStore).mockReturnValue({
        ...defaultSettingsStore,
        trainer: null,
        availableTrainers: []
    });
    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>
    );
    expect(screen.getAllByText('Treinador AI')).toHaveLength(2);
  });

  it('passes resolved trainer to the context panel', () => {
    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>
    );

    expect(screen.getByTestId('chat-context-trainer-name')).toHaveTextContent('Marcus');
  });

  it('should handle message submission', () => {
    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>
    );
    
    const input = screen.getByPlaceholderText(/Fale com seu treinador/i);
    fireEvent.change(input, { target: { value: 'New Message' } });
    
    const form = input.closest('form');
     
    if (!form) throw new Error('Form not found');
    fireEvent.submit(form);

    expect(mockSendMessage).toHaveBeenCalledWith('New Message', []);
    expect(input).toHaveValue('');
  });

  it('should prevent sending when empty or streaming', () => {
    vi.mocked(useChatStore).mockReturnValue({
        ...defaultChatStore,
        isStreaming: true
    });
    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>
    );
    const form = screen.getByTestId('chat-form');
    if (!form) throw new Error('Form not found');
    
    fireEvent.submit(form);
    expect(mockSendMessage).not.toHaveBeenCalled();
  });

  it('should display error message', () => {
    vi.mocked(useChatStore).mockReturnValue({
      ...defaultChatStore,
      error: 'default',
    });

    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>
    );
    // errors.default in pt-BR.json is "Algo deu errado..."
    expect(screen.getByText(/Algo deu errado/i)).toBeInTheDocument();
  });

  it('should handle multiline input with Shift+Enter and submit on Enter', () => {
    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>
    );
    const input = screen.getByPlaceholderText(/Fale com seu treinador/i);

    // Simulate typing 'Line1'
    fireEvent.change(input, { target: { value: 'Line1' } });

    // Simulate Shift+Enter (should not submit)
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: true });
    expect(mockSendMessage).not.toHaveBeenCalled();

    // in a real browser, the value would gain a newline, but with fireEvent/jsdom we need to update value manually or rely on component logic which we don't have for text insertion here unless using userEvent
    // However, we just want to ensure it DOES NOT submit.
    
    // Simulate Enter (should submit)
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false, code: 'Enter' });
    expect(mockSendMessage).toHaveBeenCalledWith('Line1', []);
    expect(input).toHaveValue('');
  });

  it('should display paywall when trial expired', () => {
    vi.mocked(useChatStore).mockReturnValue({
      ...defaultChatStore,
      error: 'TRIAL_EXPIRED',
    });

    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>
    );
    expect(screen.queryByPlaceholderText(/Fale com/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Teste Grátis Encerrado/i)).toBeInTheDocument();
  });

  it('should display paywall when daily limit reached', () => {
    vi.mocked(useChatStore).mockReturnValue({
      ...defaultChatStore,
      error: 'DAILY_LIMIT_REACHED',
    });

    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>
    );
    expect(screen.queryByPlaceholderText(/Fale com/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Limite Diário Atingido/i)).toBeInTheDocument();
  });
});
