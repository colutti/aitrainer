
import { Component, ChangeDetectionStrategy, inject, signal, ElementRef, viewChild, afterNextRender } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ChatService } from '../../services/chat.service';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule]
})
export class ChatComponent {
  chatService = inject(ChatService);

  newMessage = signal('');
  messages = this.chatService.messages;
  isTyping = this.chatService.isTyping;

  chatContainer = viewChild<ElementRef<HTMLDivElement>>('chatContainer');

  constructor() {
    afterNextRender(() => {
      this.scrollToBottom();
    });
  }

  sendMessage(): void {
    const text = this.newMessage().trim();
    if (text) {
      this.chatService.sendMessage(text);
      this.newMessage.set('');
      this.scrollToBottomAfterSend();
    }
  }

  private scrollToBottomAfterSend(): void {
    setTimeout(() => this.scrollToBottom(), 0);
  }

  private scrollToBottom(): void {
    const container = this.chatContainer()?.nativeElement;
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }
}
