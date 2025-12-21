import { Injectable, signal } from '@angular/core';
import { Message } from '../models/message.model';
import { HttpClient } from '@angular/common/http';
import { environment } from '../environment';
import { firstValueFrom } from 'rxjs';

/**
 * Service responsible for managing chat messages between user and AI trainer.
 * Handles message history, sending new messages, and typing indicators.
 */
@Injectable({
  providedIn: 'root',
})
export class ChatService {
  /** Signal containing the array of chat messages */
  messages = signal<Message[]>([]);

  /** Signal indicating whether the AI is currently typing a response */
  isTyping = signal<boolean>(false);

  constructor(private http: HttpClient) {
    this.resetToWelcome();
  }

  /**
   * Resets the chat to the initial welcome message.
   * Used on initialization and when clearing history.
   */
  private resetToWelcome(): void {
    this.messages.set([
      {
        id: 0,
        text: 'Olá! Eu sou seu personal trainer virtual. Como posso te ajudar a atingir seus objetivos hoje?',
        sender: 'ai',
        timestamp: new Date(),
      },
    ]);
    this.isTyping.set(false);
  }

  /**
   * Clears the chat history and resets to the welcome message.
   */
  clearHistory(): void {
    this.resetToWelcome();
  }

  /**
   * Loads message history from the backend API.
   * Messages are sorted by timestamp in ascending order.
   * On error, preserves the current messages.
   */
  async loadHistory(): Promise<void> {
    try {
      const history = await firstValueFrom(
        this.http.get<{ text: string; sender: string; timestamp?: string }[]>(
          `${environment.apiUrl}/message/history`
        )
      );
      const mapped: Message[] = [...history]
        .sort((a, b) => {
          const ta = a.timestamp ? new Date(a.timestamp).getTime() : 0;
          const tb = b.timestamp ? new Date(b.timestamp).getTime() : 0;
          return ta - tb;
        })
        .map((msg, idx) => {
          const senderStr = String(msg.sender).toLowerCase();
          const isUser = senderStr === 'student' || senderStr === 'user';
          return {
            id: idx,
            text: msg.text,
            sender: isUser ? 'user' : 'ai' as 'user' | 'ai',
            timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
          };
        });
      this.messages.set(mapped.length > 0 ? mapped : this.messages());
    } catch {
      // On error, keep the default welcome message
    }
  }

  /**
   * Sends a user message to the AI trainer and handles the streaming response.
   * Updates the messages signal with both user message and AI response in real-time.
   * Manages the typing indicator during the API call.
   * @param text - The message text to send
   */
  async sendMessage(text: string): Promise<void> {
    const userMessage: Message = {
      id: Date.now(),
      text,
      sender: 'user',
      timestamp: new Date(),
    };
    this.messages.update((msgs) => [...msgs, userMessage]);

    // Create an initial empty AI message
    const aiMessageId = Date.now() + 1;
    const aiMessage: Message = {
      id: aiMessageId,
      text: '',
      sender: 'ai',
      timestamp: new Date(),
    };
    this.messages.update((msgs) => [...msgs, aiMessage]);
    this.isTyping.set(true);

    try {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch(`${environment.apiUrl}/message/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ user_message: text }),
      });

      if (!response.ok) {
        throw new Error('Falha na comunicação com o servidor');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          accumulatedText += decoder.decode(value, { stream: true });

          // Update the specific AI message with the newly arrived text
          this.messages.update((msgs) =>
            msgs.map((m) =>
              m.id === aiMessageId ? { ...m, text: accumulatedText } : m
            )
          );
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
      this.messages.update((msgs) =>
        msgs.map((m) =>
          m.id === aiMessageId
            ? { ...m, text: 'Erro ao se comunicar com o servidor.' }
            : m
        )
      );
    } finally {
      this.isTyping.set(false);
    }
  }

}

