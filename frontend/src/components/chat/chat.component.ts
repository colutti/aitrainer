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
    // In flex-col-reverse, scrollTop is negative or 0 depending on browser
    // or checks scrollHeight vs scrollTop.
    // Actually, usually 0 is bottom in flex-col-reverse? No, 0 is top.
    // Wait, flex-col-reverse makes the content start from bottom, but the scrollbar is still standard?
    // Chrome: scrollTop is 0 at top, max at bottom.
    // If flex-col-reverse, content is reversed.
    // Let's assume standard behavior: we want to show button if user scrolls UP from bottom.
    // Bottom means (scrollHeight - scrollTop - clientHeight) < threshold.
    
    // Simplification: if scrollTop < (scrollHeight - clientHeight - 100), show button.
    const isAtBottom = Math.abs(el.scrollHeight - el.scrollTop - el.clientHeight) < 50;
    this.showScrollButton.set(!isAtBottom);
  }

  scrollToBottom() {
    // In flex-col-reverse, new messages are at the "bottom" visually which is the beginning of the container?
    // Wait, <div class="flex-col-reverse"> puts the *last* DOM element at the *top* visually?
    // No. flex-direction: column-reverse;
    // Item 1 (DOM) -> Bottom (Visual)
    // Item N (DOM) -> Top (Visual)
    // My template iterates reversedMessages().
    // reversedMessages() = [...messages].reverse(). 
    // So Message[Last] (Newest) is at index 0 of array.
    // So it renders first in DOM?
    
    // If I use flex-col-reverse:
    // DOM: [Newest, ..., Oldest]
    // Visual: 
    //   Oldest
    //   ...
    //   Newest
    
    // Wait, standard chat is:
    // Oldest (Top)
    // Newest (Bottom)
    
    // If I use flex-col-reverse on the container:
    // Visual Top: Last DOM Element
    // Visual Bottom: First DOM Element
    
    // If my array is `reversedMessages` (Newest first):
    // DOM:
    //  <div>Newest</div>
    //  ...
    //  <div>Oldest</div>
    
    // Visual (column-reverse):
    //  Top: Oldest
    //  Bottom: Newest
    
    // So "Bottom" visual is "Top" of Scroll logic?
    // Because DOM First Element is at Visual Bottom.
    // So scrollTop 0 should be... the content top (Oldest)? 
    
    // Actually, with flex-col-reverse, `scrollTop: 0` is usually the top of the container (Oldest).
    // The "Bottom" (Newest) is at scrollTop = scrollHeight.
    
    // Wait, usually flex-col-reverse is used so that when content grows, it stays anchored to bottom?
    // If I verify the template:
    // <div class="flex-1 overflow-y-auto flex flex-col-reverse">
    //   <div class="max-w-3xl ... flex flex-col-reverse gap-6">
    //      @for message of reversedMessages
    
    // So we have an outer scroll container, and inner wrapper.
    // Inner wrapper has flex-col-reverse.
    
    // To scroll to bottom (Visual Newest), we need to scroll to... ?
    // If visual bottom is where "Newest" is.
    // Newest is DOM First Child?
    // flex-col-reverse:
    // | Container |
    // | Item 3    |
    // | Item 2    |
    // | Item 1    |
    
    // If I want to see Item 1 (Newest), I look at the bottom.
    // That corresponds to `scrollTop` being max (if standard scrollbar).
    
    // I will simply try: `el.scrollTop = el.scrollHeight;` and see.
    // The button should appear if `scrollTop < max`.
    
    const container = document.querySelector('.chat-scroll-container'); 
    if (container) {
      container.scrollTop = container.scrollHeight;
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
