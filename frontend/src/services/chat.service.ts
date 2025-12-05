
import { Injectable, signal, inject } from '@angular/core';
import { Message } from '../models/message.model';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../environment';
import { AuthService } from './auth.service';
import { firstValueFrom } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class ChatService {

  messages = signal<Message[]>([]);
  isTyping = signal<boolean>(false);

  constructor(private http: HttpClient, private auth: AuthService) {
    this.messages.set([
      {
        id: 0,
        text: 'Olá! Eu sou seu personal trainer virtual. Como posso te ajudar a atingir seus objetivos hoje?',
        sender: 'ai',
        timestamp: new Date(),
      },
    ]);
  }


  async sendMessage(text: string): Promise<void> {
    const userMessage: Message = {
      id: this.messages().length,
      text,
      sender: 'user',
      timestamp: new Date(),
    };
    this.messages.update(msgs => [...msgs, userMessage]);
    this.isTyping.set(true);

    try {
      const response = await firstValueFrom(
        this.http.post<{ response: string }>(`${environment.apiUrl}/message`, { user_message: text })
      );
      const aiMessage: Message = {
        id: this.messages().length,
        text: response?.response || 'Erro ao obter resposta do servidor.',
        sender: 'ai',
        timestamp: new Date(),
      };
      this.messages.update(msgs => [...msgs, aiMessage]);
    } catch (error) {
      const aiMessage: Message = {
        id: this.messages().length,
        text: 'Erro ao se comunicar com o servidor.',
        sender: 'ai',
        timestamp: new Date(),
      };
      this.messages.update(msgs => [...msgs, aiMessage]);
    } finally {
      this.isTyping.set(false);
    }
  }

  // Removed mock response logic; now uses backend API
}
