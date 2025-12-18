import { Component, ChangeDetectionStrategy, inject, signal, ElementRef, viewChild, afterNextRender, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ChatService } from '../../services/chat.service';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule]
})
export class ChatComponent implements OnInit {
  // Dependencies
  private chatService = inject(ChatService);

  // Signals and Properties
  newMessage = signal('');
  messages = this.chatService.messages;
  isTyping = this.chatService.isTyping;
  chatContainer = viewChild<ElementRef<HTMLDivElement>>('chatContainer');

  // Constructor
  constructor() {
    afterNextRender(() => this.scrollToBottom());
  }

  // Lifecycle Hooks
  async ngOnInit(): Promise<void> {
    await this.chatService.loadHistory();
  }

  // Public Methods
  sendMessage(): void {
    const text = this.newMessage().trim();
    if (text) {
      this.chatService.sendMessage(text);
      this.newMessage.set('');
      this.scrollToBottomAfterSend();
    }
  }

  // Private Methods
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
