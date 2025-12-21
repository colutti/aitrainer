import {
  Component,
  ChangeDetectionStrategy,
  inject,
  signal,
  computed,
  viewChild,
  ElementRef,
  OnInit,
  ChangeDetectorRef
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ChatService } from '../../services/chat.service';
import { MarkdownPipe } from '../../pipes/markdown.pipe';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule, MarkdownPipe],
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
}
