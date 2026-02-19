import { User, Bot } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { UserAvatar } from '../../../shared/components/ui/UserAvatar';
import { type ChatMessage } from '../../../shared/types/chat';
import { cn } from '../../../shared/utils/cn';

interface MessageBubbleProps {
  message: ChatMessage;
  trainerId?: string;
  userPhoto?: string;
  userName?: string;
}

/**
 * MessageBubble component
 *
 * Displays a single chat message with different styling based on the sender.
 * Supports Markdown rendering for AI responses.
 */
export function MessageBubble({ message, trainerId, userPhoto, userName }: MessageBubbleProps) {
  const isUser = message.sender === 'Student';

  return (
    <div className={cn(
      'flex w-full gap-3 animate-in fade-in slide-in-from-bottom-2 duration-300',
      isUser ? 'flex-row-reverse' : 'flex-row'
    )}>
      {/* Avatar */}
      {isUser && userPhoto ? (
        <UserAvatar photo={userPhoto} name={userName} size="sm" className="shrink-0" />
      ) : (
        <div className={cn(
          'shrink-0 w-8 h-8 rounded-full flex items-center justify-center overflow-hidden',
          isUser ? 'bg-gradient-start text-white' : 'bg-dark-bg border border-border text-gradient-start'
        )}>
          {isUser ? (
            <User size={18} />
          ) : trainerId ? (
            <img
              src={`/assets/avatars/${trainerId.toLowerCase()}.png`}
              alt="Trainer"
              className="w-full h-full object-cover"
            />
          ) : (
            <Bot size={18} />
          )}
        </div>
      )}

      {/* Bubble */}
      <div className={cn(
        "max-w-[85%] md:max-w-[70%] rounded-2xl p-4 shadow-sm text-sm leading-relaxed",
        isUser 
          ? "bg-gradient-start text-white rounded-tr-none" 
          : "bg-dark-card border border-border text-text-primary rounded-tl-none"
      )}>
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.text}</p>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-dark-bg/50 prose-pre:border prose-pre:border-border/50">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.text}</ReactMarkdown>
            {message.text === '' && (
              <div className="flex gap-1 mt-1">
                <div className="w-1.5 h-1.5 bg-gradient-start rounded-full animate-bounce" />
                <div className="w-1.5 h-1.5 bg-gradient-start rounded-full animate-bounce delay-75" />
                <div className="w-1.5 h-1.5 bg-gradient-start rounded-full animate-bounce delay-150" />
              </div>
            )}
          </div>
        )}
        
        <div className={cn(
          "text-[10px] mt-2 opacity-50",
          isUser ? "text-right" : "text-left"
        )}>
          {new Date(message.timestamp).toLocaleString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      </div>
    </div>
  );
}
