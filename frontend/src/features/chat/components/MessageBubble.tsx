import { motion } from 'framer-motion';
import { Bot, User } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';

import { type ChatMessage } from '../../../shared/types/chat';
import { cn } from '../../../shared/utils/cn';

interface MessageBubbleProps {
  message: ChatMessage;
  resolveText?: (message: ChatMessage) => string;
  trainerId?: string;
  userPhoto?: string;
  userName?: string;
}

/**
 * MessageBubble component
 * 
 * Renders an individual chat message with premium glassmorphism aesthetic,
 * Markdown support, and smooth Framer Motion animations.
 */
export function MessageBubble({ message, resolveText, trainerId, userPhoto, userName }: MessageBubbleProps) {
  const { t } = useTranslation();
  const isTrainer = message.sender === 'Trainer';
  const displayText = resolveText ? resolveText(message) : message.text;
  const isEmpty = !displayText || displayText.trim() === '';

  const containerVariants = {
    hidden: { opacity: 0, y: 10, scale: 0.95 },
    visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.3 } }
  };

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      data-testid="chat-message"
      className={cn(
        "flex w-full gap-4 items-end mb-6",
        isTrainer ? "flex-row" : "flex-row-reverse"
      )}
    >
      {/* AVATAR */}
      <div data-testid="chat-message-avatar" className="flex flex-none mb-1">
        <div className={cn(
          "w-10 h-10 rounded-2xl border flex items-center justify-center overflow-hidden shadow-lg",
          isTrainer 
            ? "bg-zinc-900 border-white/5 text-indigo-400" 
            : "bg-indigo-500 border-white/10 text-white"
        )}>
          {isTrainer ? (
            trainerId ? (
              <img src={`/assets/avatars/${trainerId.toLowerCase()}.png`} alt="Trainer" className="w-full h-full object-cover" />
            ) : <Bot size={20} />
          ) : (
            userPhoto ? (
              <img src={userPhoto} alt="Me" className="w-full h-full object-cover" />
            ) : <User size={20} />
          )}
        </div>
      </div>

      {/* BUBBLE */}
      <div className={cn(
        "flex flex-col max-w-full lg:max-w-[80%] xl:max-w-[70%]",
        isTrainer ? "items-start" : "items-end"
      )} data-testid="chat-message-bubble">
        <span className="text-[10px] font-black uppercase tracking-widest text-zinc-600 mb-1.5 ml-1">
          {isTrainer ? (trainerId ?? 'AI Trainer') : (userName ?? t('common.athlete'))}
        </span>
        
        <div className={cn(
          "px-5 py-4 rounded-[24px] relative overflow-hidden",
          isTrainer 
            ? "bg-white/[0.03] backdrop-blur-2xl border border-white/5 rounded-bl-none text-zinc-200" 
            : "bg-gradient-to-br from-indigo-500 to-indigo-600 border border-white/10 rounded-br-none text-white shadow-xl shadow-indigo-500/10"
        )}>
          {isTrainer && (
            <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-indigo-500/5 to-transparent pointer-events-none" />
          )}
          
          <div className="prose prose-invert prose-sm max-w-none font-medium leading-relaxed selection:bg-white/20">
             {isEmpty && isTrainer ? (
               <div className="flex gap-1 py-2 px-1">
                 <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                 <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                 <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
               </div>
             ) : (
               <ReactMarkdown>{displayText}</ReactMarkdown>
             )}
          </div>
        </div>
        
        <span className="text-[9px] font-bold text-zinc-700 mt-1.5 uppercase tracking-tighter">
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </motion.div>
  );
}
