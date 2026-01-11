import {
  Component,
  ChangeDetectionStrategy,
  inject,
  signal,
  computed,
  OnInit,
  AfterViewChecked,
  ChangeDetectorRef,
  ViewChild,
  ElementRef
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ChatService } from '../../services/chat.service';
import { MarkdownComponent } from 'ngx-markdown';

import { ViewEncapsulation } from '@angular/core';

import { TrainerProfileService } from '../../services/trainer-profile.service';
import { UserProfileService } from '../../services/user-profile.service';
import { TrainerCard } from '../../models/trainer-profile.model';

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

    /* Chat textarea styling - height managed by JS */
    .chat-textarea {
      line-height: 1.5;
    }
  `]
})
export class ChatComponent implements OnInit, AfterViewChecked {
  private chatService = inject(ChatService);
  private trainerProfileService = inject(TrainerProfileService);
  private userProfileService = inject(UserProfileService);
  private cdr = inject(ChangeDetectorRef);

  @ViewChild('messageInput') messageInput!: ElementRef<HTMLTextAreaElement>;

  newMessage = signal('');
  messages = this.chatService.messages;
  isTyping = this.chatService.isTyping;
  
  availableTrainers = signal<TrainerCard[]>([]);
  trainerProfile = signal<any>(null); // Using any temporarily or better TrainerProfile
  
  showScrollButton = signal(false);
  
  // Suggestion chips
  suggestions = [
    "Me sugira um treino de pernas",
    "Como melhorar meu supino?",
    "Quero dicas de nutrição para hipertrofia",
    "Explique o princípio da sobrecarga progressiva"
  ];

  // Computed trainer based on fetched profile
  currentTrainer = computed(() => {
    const profile = this.trainerProfile();
    const type = profile?.trainer_type;
    return this.availableTrainers().find(t => t.trainer_id === type);
  });

  // Computed signal to reverse messages for the flex-col-reverse layout
  reversedMessages = computed(() => {
    return [...this.messages()].reverse();
  });

  async ngOnInit(): Promise<void> {
    const [_, trainers, profile] = await Promise.all([
      this.chatService.loadHistory(),
      this.trainerProfileService.getAvailableTrainers(),
      this.trainerProfileService.fetchProfile()
    ]);
    
    this.availableTrainers.set(trainers);
    this.trainerProfile.set(profile);
    
    this.cdr.markForCheck();
  }

  private shouldResetHeight = false;

  sendMessage(): void {
    const text = this.newMessage().trim();
    if (text) {
      this.chatService.sendMessage(text);
      this.newMessage.set('');
      this.shouldResetHeight = true;
      this.cdr.detectChanges();
    }
  }

  ngAfterViewChecked(): void {
    if (this.shouldResetHeight && this.messageInput) {
      const textarea = this.messageInput.nativeElement;
      textarea.style.height = '56px';
      textarea.style.overflowY = 'hidden';
      this.shouldResetHeight = false;
    }
  }

  /**
   * Handles keyboard events in the message textarea.
   * - Enter alone: sends the message
   * - Shift+Enter: allows default behavior (new line)
   */
  sendSuggestion(text: string) {
    this.newMessage.set(text);
    this.sendMessage();
  }

  onScroll(event: Event) {
    const el = event.target as HTMLElement;
    // With flex-col-reverse:
    // - scrollTop = 0 means we're at the VISUAL BOTTOM (newest messages)
    // - scrollTop > 0 means we've scrolled UP towards older messages
    // 
    // We want to show the scroll button when user has scrolled UP (away from bottom)
    const isAtBottom = el.scrollTop < 50; // Near 0 = at visual bottom
    this.showScrollButton.set(!isAtBottom);
  }

  scrollToBottom() {
    // With flex-col-reverse, scrollTop = 0 is the visual bottom (newest messages)
    const container = document.querySelector('.chat-scroll-container'); 
    if (container) {
      container.scrollTop = 0;
    }
  }

  handleKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  /**
   * Auto-adjusts textarea height based on content.
   * Called on input events.
   */
  adjustTextareaHeight(): void {
    if (this.messageInput) {
      const textarea = this.messageInput.nativeElement;
      const maxHeight = 200;
      
      // Reset to auto to get the natural scrollHeight
      textarea.style.height = 'auto';
      
      // Set height based on content, capped at max
      const newHeight = Math.min(textarea.scrollHeight, maxHeight);
      textarea.style.height = newHeight + 'px';
      
      // Show scrollbar only when content exceeds max height
      textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden';
    }
  }
}
