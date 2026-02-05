import { User, Bot } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

import { type ChatMessage } from '../../../shared/types/chat';
import { cn } from '../../../shared/utils/cn';

interface MessageBubbleProps {
  message: ChatMessage;
}

/**
 * MessageBubble component
 * 
 * Displays a single chat message with different styling based on the sender.
 * Supports Markdown rendering for AI responses.
 */
export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.sender === 'Student';

  return (
    <div className={cn(
      "flex w-full gap-3 animate-in fade-in slide-in-from-bottom-2 duration-300",
      isUser ? "flex-row-reverse" : "flex-row"
    )}>
      {/* Avatar */}
      <div className={cn(
        "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
        isUser ? "bg-gradient-start text-white" : "bg-dark-bg border border-border text-gradient-start"
      )}>
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>

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
            <ReactMarkdown>{message.text}</ReactMarkdown>
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
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
}
