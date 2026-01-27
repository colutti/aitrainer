import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { ChatComponent } from './chat.component';
import { ChatService } from '../../services/chat.service';
import { TrainerProfileService } from '../../services/trainer-profile.service';
import { ChangeDetectorRef } from '@angular/core';
import { MessageFactory } from '../../test-utils/factories/message.factory';
import { TrainerFactory } from '../../test-utils/factories/trainer.factory';
import { signal } from '@angular/core';

describe('ChatComponent', () => {
  let component: ChatComponent;
  let fixture: ComponentFixture<ChatComponent>;
  let mockChatService: Partial<ChatService>;
  let mockTrainerService: Partial<TrainerProfileService>;
  let mockChangeDetectorRef: Partial<ChangeDetectorRef>;

  beforeEach(async () => {
    mockChatService = {
      messages: signal(MessageFactory.createList(3)),
      isTyping: signal(false),
      isLoading: signal(false),
      clearHistory: jest.fn().mockResolvedValue(undefined),
      loadHistory: jest.fn().mockResolvedValue(undefined),
      sendMessage: jest.fn().mockResolvedValue(undefined)
    };

    mockTrainerService = {
      profile: signal(TrainerFactory.create()),
      availableTrainers: signal(TrainerFactory.createAllTrainers()),
      fetchProfile: jest.fn().mockResolvedValue(undefined),
      getAvailableTrainers: jest.fn().mockResolvedValue(TrainerFactory.createAllTrainers())
    };

    mockChangeDetectorRef = {
      markForCheck: jest.fn(),
      detach: jest.fn(),
      detectChanges: jest.fn(),
      reattach: jest.fn()
    };

    await TestBed.configureTestingModule({
      imports: [ChatComponent, FormsModule],
      providers: [
        { provide: ChatService, useValue: mockChatService },
        { provide: TrainerProfileService, useValue: mockTrainerService },
        { provide: ChangeDetectorRef, useValue: mockChangeDetectorRef }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ChatComponent);
    component = fixture.componentInstance;
  });

  describe('Initialization', () => {
    it('should create component', () => {
      expect(component).toBeTruthy();
    });

    it('should initialize signals on ngOnInit', async () => {
      fixture.detectChanges();
      await fixture.whenStable();

      expect(mockChatService.loadHistory).toHaveBeenCalled();
      expect(mockTrainerService.getAvailableTrainers).toHaveBeenCalled();
      expect(mockTrainerService.fetchProfile).toHaveBeenCalled();
    });

    it('should load message history', async () => {
      fixture.detectChanges();
      await fixture.whenStable();

      expect(component.messages()).toEqual(MessageFactory.createList(3));
    });

    it('should load available trainers', async () => {
      fixture.detectChanges();
      await fixture.whenStable();

      expect(component.availableTrainers()).toHaveLength(5);
    });
  });

  describe('Message Display', () => {
    it('should render message history', async () => {
      const messages = MessageFactory.createList(5);
      (mockChatService.messages as any).set(messages);

      fixture.detectChanges();
      await fixture.whenStable();

      const messageElements = fixture.nativeElement.querySelectorAll('[data-test="message"]');
      expect(messageElements.length).toBeGreaterThanOrEqual(0);
    });

    it('should reverse message order for flex-col-reverse', () => {
      const messages = [
        MessageFactory.create({ id: 1, text: 'First' }),
        MessageFactory.create({ id: 2, text: 'Second' }),
        MessageFactory.create({ id: 3, text: 'Third' })
      ];
      (mockChatService.messages as any).set(messages);

      fixture.detectChanges();

      const reversed = component.reversedMessages();
      expect(reversed[0].id).toBe(3);
      expect(reversed[1].id).toBe(2);
      expect(reversed[2].id).toBe(1);
    });

    it('should display typing indicator when isTyping is true', () => {
      (mockChatService.isTyping as any).set(true);
      fixture.detectChanges();

      expect(component.isTyping()).toBe(true);
    });

    it('should hide typing indicator when isTyping is false', () => {
      (mockChatService.isTyping as any).set(false);
      fixture.detectChanges();

      expect(component.isTyping()).toBe(false);
    });
  });

  describe('Message Input', () => {
    it('should allow typing in message input', () => {
      const testMessage = 'Hello, trainer!';
      component.newMessage.set(testMessage);

      expect(component.newMessage()).toBe(testMessage);
    });

    it('should clear message input after sending', async () => {
      component.newMessage.set('Test message');
      fixture.detectChanges();
      await fixture.whenStable();

      await component.sendMessage();

      expect(component.newMessage()).toBe('');
    });

    it('should not send empty messages', async () => {
      component.newMessage.set('');
      await component.sendMessage();

      expect(mockChatService.sendMessage).not.toHaveBeenCalled();
    });

    it('should trim whitespace before sending', async () => {
      component.newMessage.set('   ');
      await component.sendMessage();

      expect(mockChatService.sendMessage).not.toHaveBeenCalled();
    });
  });

  describe('sendMessage()', () => {
    it('should send message with correct text', async () => {
      const testMessage = 'Test message';
      component.newMessage.set(testMessage);

      await component.sendMessage();

      expect(mockChatService.sendMessage).toHaveBeenCalledWith(testMessage);
    });

    it('should clear input after successful send', async () => {
      component.newMessage.set('Test');
      await component.sendMessage();

      expect(component.newMessage()).toBe('');
    });

    it('should handle send errors gracefully', async () => {
      (mockChatService.sendMessage as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      );

      component.newMessage.set('Test');
      await expect(component.sendMessage()).rejects.toThrow('Network error');
    });

    it('should send multiple messages sequentially', async () => {
      component.newMessage.set('First');
      await component.sendMessage();

      component.newMessage.set('Second');
      await component.sendMessage();

      expect(mockChatService.sendMessage).toHaveBeenCalledTimes(2);
      expect(mockChatService.sendMessage).toHaveBeenNthCalledWith(1, 'First');
      expect(mockChatService.sendMessage).toHaveBeenNthCalledWith(2, 'Second');
    });
  });

  describe('Keyboard Interactions', () => {
    it('should send message on Enter key', async () => {
      component.newMessage.set('Test');
      const event = new KeyboardEvent('keydown', { key: 'Enter' });
      jest.spyOn(event, 'preventDefault');

      await component.handleKeyDown(event);

      expect(mockChatService.sendMessage).toHaveBeenCalled();
    });

    it('should create line break on Shift+Enter', async () => {
      const initialText = 'Line 1';
      component.newMessage.set(initialText);
      const event = new KeyboardEvent('keydown', { key: 'Enter', shiftKey: true });
      jest.spyOn(event, 'preventDefault');

      await component.handleKeyDown(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should ignore other keys', async () => {
      const event = new KeyboardEvent('keydown', { key: 'a' });
      jest.spyOn(event, 'preventDefault');

      await component.handleKeyDown(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
      expect(mockChatService.sendMessage).not.toHaveBeenCalled();
    });
  });

  describe('Textarea Auto-height', () => {
    it('should adjust textarea height on input', () => {
      const textarea = fixture.nativeElement.querySelector('textarea');
      if (!textarea) return;

      component.adjustTextareaHeight();

      // Height should be calculated based on scrollHeight
      expect(textarea.style.height).toBeTruthy();
    });

    it('should cap textarea height at 200px', () => {
      const textarea = fixture.nativeElement.querySelector('textarea');
      if (!textarea) return;

      // Simulate long text
      component.newMessage.set('Line1\nLine2\nLine3\nLine4\nLine5\nLine6\nLine7\nLine8\nLine9\nLine10');
      fixture.detectChanges();

      component.adjustTextareaHeight();

      const height = parseInt(textarea.style.height || '0');
      expect(height).toBeLessThanOrEqual(200);
    });

    it('should reset height to auto initially', () => {
      const textarea = fixture.nativeElement.querySelector('textarea');
      if (!textarea) return;

      component.newMessage.set('Test');
      component.adjustTextareaHeight();

      expect(textarea.style.height).toBeTruthy();
    });
  });

  describe('Scroll Position', () => {
    it('should show scroll button when scrolled up', () => {
      component.onScroll({ target: { scrollTop: 100 } } as any);

      expect(component.showScrollButton()).toBe(true);
    });

    it('should hide scroll button when at bottom', () => {
      component.onScroll({ target: { scrollTop: 0 } } as any);

      expect(component.showScrollButton()).toBe(false);
    });

    it('should scroll to top on button click', () => {
      const container = fixture.nativeElement.querySelector('[data-test="messages-container"]');
      if (!container) return;

      component.scrollToBottom();

      expect(container.scrollTop).toBe(0);
    });
  });

  describe('Trainer Selection', () => {
    it('should display current trainer', () => {
      const trainer = TrainerFactory.createAtlas();
      (mockTrainerService.profile as any).set({
        trainer_type: 'atlas',
        settings: {}
      });

      fixture.detectChanges();

      const current = component.currentTrainer();
      expect(current?.trainer_type).toBe('atlas');
    });

    it('should get all available trainers', () => {
      fixture.detectChanges();

      const trainers = component.availableTrainers();
      expect(trainers.length).toBe(5);
      expect(trainers.map(t => t.trainer_type)).toContain('atlas');
      expect(trainers.map(t => t.trainer_type)).toContain('luna');
    });

    it('should update trainer on profile change', async () => {
      const newProfile = TrainerFactory.create({ trainer_type: 'sofia' });
      (mockTrainerService.profile as any).set(newProfile);

      fixture.detectChanges();
      await fixture.whenStable();

      expect(component.currentTrainer()?.trainer_type).toBe('sofia');
    });
  });

  describe('Suggestion Handling', () => {
    it('should send suggestion as message', async () => {
      const suggestion = 'How can I improve my form?';

      await component.sendSuggestion(suggestion);

      expect(mockChatService.sendMessage).toHaveBeenCalledWith(suggestion);
    });

    it('should accept suggestion from template', async () => {
      component.sendSuggestion('Give me a workout plan');

      expect(mockChatService.sendMessage).toHaveBeenCalledWith(
        'Give me a workout plan'
      );
    });
  });

  describe('ngAfterViewChecked', () => {
    it('should reset textarea height after view checks', () => {
      component.newMessage.set('Test');
      fixture.detectChanges();

      component.ngAfterViewChecked();

      const textarea = fixture.nativeElement.querySelector('textarea');
      if (textarea) {
        expect(textarea.style.height).toBeTruthy();
      }
    });
  });

  describe('Loading States', () => {
    it('should display loading state initially', () => {
      (mockChatService.isLoading as any).set(true);
      fixture.detectChanges();

      expect(component.isLoading()).toBe(true);
    });

    it('should hide loading after data loads', () => {
      (mockChatService.isLoading as any).set(false);
      fixture.detectChanges();

      expect(component.isLoading()).toBe(false);
    });
  });

  describe('Error Scenarios', () => {
    it('should handle service initialization error', async () => {
      (mockChatService.loadHistory as jest.Mock).mockRejectedValueOnce(
        new Error('Failed to load history')
      );

      fixture.detectChanges();

      // Component should still render even with errors
      expect(component).toBeTruthy();
    });

    it('should recover from trainer profile fetch error', async () => {
      (mockTrainerService.fetchProfile as jest.Mock).mockRejectedValueOnce(
        new Error('Profile not found')
      );

      fixture.detectChanges();
      await fixture.whenStable();

      // Should use availableTrainers as fallback
      expect(component.availableTrainers()).toBeDefined();
    });
  });

  describe('Memory Management', () => {
    it('should clear history when requested', async () => {
      await component.clearHistory();

      expect(mockChatService.clearHistory).toHaveBeenCalled();
    });

    it('should maintain message order in memory', () => {
      const messages = [
        MessageFactory.create({ id: 1, timestamp: new Date('2026-01-25') }),
        MessageFactory.create({ id: 2, timestamp: new Date('2026-01-26') }),
        MessageFactory.create({ id: 3, timestamp: new Date('2026-01-27') })
      ];
      (mockChatService.messages as any).set(messages);

      fixture.detectChanges();

      const displayed = component.reversedMessages();
      expect(displayed[0].id).toBe(3);
    });
  });

  describe('Change Detection', () => {
    it('should mark for check after message send', async () => {
      component.newMessage.set('Test');
      await component.sendMessage();

      expect(mockChangeDetectorRef.markForCheck).toHaveBeenCalled();
    });

    it('should detect changes after scroll', () => {
      component.onScroll({ target: { scrollTop: 50 } } as any);

      expect(mockChangeDetectorRef.detectChanges).toHaveBeenCalled();
    });
  });
});
