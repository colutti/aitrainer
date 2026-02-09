import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useChatStore } from '../../shared/hooks/useChat';
import { useSettingsStore } from '../../shared/hooks/useSettings';

import { ChatPage } from './ChatPage';

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
    render(<ChatPage />);
    expect(screen.getByText('Inicie sua conversa')).toBeInTheDocument();
  });

  it('should fetch trainer and available trainers if empty', () => {
    vi.mocked(useSettingsStore).mockReturnValue({
        ...defaultSettingsStore,
        availableTrainers: []
    });
    render(<ChatPage />);
    expect(mockFetchTrainer).toHaveBeenCalled();
    expect(mockFetchAvailable).toHaveBeenCalled();
  });

  it('should render default trainer name when trainer not found', () => {
    vi.mocked(useSettingsStore).mockReturnValue({
        ...defaultSettingsStore,
        trainer: null,
        availableTrainers: []
    });
    render(<ChatPage />);
    expect(screen.getByText('Treinador AI')).toBeInTheDocument();
  });

  it('should handle message submission', () => {
    render(<ChatPage />);
    
    const input = screen.getByPlaceholderText(/Mensagem para Marcus/i);
    fireEvent.change(input, { target: { value: 'New Message' } });
    
    const form = input.closest('form');
     
    if (!form) throw new Error('Form not found');
    fireEvent.submit(form);

    expect(mockSendMessage).toHaveBeenCalledWith('New Message');
    expect(input).toHaveValue('');
  });

  it('should prevent sending when empty or streaming', () => {
    vi.mocked(useChatStore).mockReturnValue({
        ...defaultChatStore,
        isStreaming: true
    });
    render(<ChatPage />);
    const button = screen.getByRole('button');
    const form = button.closest('form');
    if (!form) throw new Error('Form not found');
    
    fireEvent.submit(form);
    expect(mockSendMessage).not.toHaveBeenCalled();
  });

  it('should display error message', () => {
    vi.mocked(useChatStore).mockReturnValue({
      ...defaultChatStore,
      error: 'Failed to send',
    });

    render(<ChatPage />);
    expect(screen.getByText('Failed to send')).toBeInTheDocument();
  });

  it('should handle multiline input with Shift+Enter and submit on Enter', () => {
    render(<ChatPage />);
    const input = screen.getByPlaceholderText(/Mensagem para Marcus/i);

    // Simulate typing 'Line1'
    fireEvent.change(input, { target: { value: 'Line1' } });

    // Simulate Shift+Enter (should not submit)
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: true });
    expect(mockSendMessage).not.toHaveBeenCalled();

    // in a real browser, the value would gain a newline, but with fireEvent/jsdom we need to update value manually or rely on component logic which we don't have for text insertion here unless using userEvent
    // However, we just want to ensure it DOES NOT submit.
    
    // Simulate Enter (should submit)
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false });
    expect(mockSendMessage).toHaveBeenCalledWith('Line1');
    expect(input).toHaveValue('');
  });
});

