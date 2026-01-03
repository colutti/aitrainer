import {
  Component,
  ChangeDetectionStrategy,
  inject,
  signal,
  computed,
  OnInit,
  ChangeDetectorRef
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ChatService } from '../../services/chat.service';
import { MarkdownComponent } from 'ngx-markdown';

import { ViewEncapsulation } from '@angular/core';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule, MarkdownComponent],
  encapsulation: ViewEncapsulation.None,
  styles: [`
    .markdown-content {
      line-height: 1.6;
    }

    .markdown-content strong {
      font-weight: 600;
    }

    .markdown-content ol {
      list-style-type: decimal;
      margin-left: 1.5rem;
      margin-top: 0.5rem;
      margin-bottom: 0.5rem;
    }

    .markdown-content ul {
      list-style-type: disc;
      margin-left: 1.5rem;
      margin-top: 0.5rem;
      margin-bottom: 0.5rem;
    }

    .markdown-content li {
      margin-bottom: 0.25rem;
    }

    .markdown-content p {
      margin-bottom: 0.5rem;
    }

    .markdown-content p:last-child {
      margin-bottom: 0;
    }

    /* Simple Code blocks styling */
    .markdown-content pre {
      background-color: #2d2d2d;
      border-radius: 0.5rem;
      padding: 1rem;
      margin: 0.5rem 0;
      overflow-x: auto;
      max-width: 100%;
    }

    .markdown-content pre code {
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 0.875rem;
      line-height: 1.5;
      color: #f8f8f2;
      background-color: transparent;
      padding: 0;
      white-space: pre;
    }

    /* Inline code styling */
    .markdown-content code:not(pre code) {
      background-color: rgba(110, 118, 129, 0.4);
      padding: 0.2em 0.4em;
      border-radius: 0.25rem;
      font-size: 0.875em;
    }
  `]
})
export class ChatComponent implements OnInit {
  private chatService = inject(ChatService);
  private cdr = inject(ChangeDetectorRef);

  newMessage = signal('');
  messages = this.chatService.messages;
  isTyping = this.chatService.isTyping;

  // Computed signal to reverse messages for the flex-col-reverse layout
  // This is the most robust way to keep a chat at the bottom without complex JS.
  reversedMessages = computed(() => {
    return [...this.messages()].reverse();
  });

  async ngOnInit(): Promise<void> {
    await this.chatService.loadHistory();
    this.cdr.markForCheck();
  }

  sendMessage(): void {
    const text = this.newMessage().trim();
    if (text) {
      this.chatService.sendMessage(text);
      this.newMessage.set('');
    }
  }

  /**
   * Handles keyboard events in the message textarea.
   * - Enter alone: sends the message
   * - Shift+Enter: allows default behavior (new line)
   */
  handleKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      // Enter without Shift: send message
      event.preventDefault();
      this.sendMessage();
    }
    // Shift+Enter: let the browser's default textarea behavior insert a new line
  }

  /**
   * Auto-resizes the textarea based on content.
   * Called on input events.
   */
  autoResize(textarea: HTMLTextAreaElement): void {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
  }

  /**
   * Handles input events for auto-resize.
   */
  onInput(event: Event): void {
    const textarea = event.target as HTMLTextAreaElement;
    this.autoResize(textarea);
  }
}
