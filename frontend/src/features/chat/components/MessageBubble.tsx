import { motion } from 'framer-motion';
import { Bot, User } from 'lucide-react';
import { memo } from 'react';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { type ChatMessage } from '../../../shared/types/chat';
import { cn } from '../../../shared/utils/cn';

interface MessageBubbleProps {
  message: ChatMessage;
  resolveText?: (message: ChatMessage) => string;
  trainerId?: string;
  userPhoto?: string;
  userName?: string;
}

function normalizeMarkdownText(text: string): string {
  let normalized = text;

  // Normalize common pipe/whitespace encodings seen in persisted historical payloads.
  normalized = normalized
    .replaceAll('\\u007c', '|')
    .replaceAll('\\U007C', '|')
    .replaceAll('&#124;', '|')
    .replaceAll('&#x7C;', '|')
    .replaceAll('｜', '|')
    .replaceAll('│', '|')
    .replace(/[\u200B-\u200D\uFEFF]/g, '');

  if (normalized.includes('\\')) {
    // Some production responses can arrive with escaped markdown characters.
    // Normalize common escaped sequences so GFM tables/lists render properly.
    normalized = normalized
    .replaceAll('\\r\\n', '\n')
    .replaceAll('\\n', '\n')
    .replaceAll('\\r', '\n')
    .replaceAll('\\|', '|');
  }

  const looksLikeSingleLineTable = /\|\s*:?-{3,}\s*\|/.test(normalized);

  if (looksLikeSingleLineTable) {
    // Some model responses flatten all table rows into one line using "| |" row separators.
    // Rebuild line breaks so remark-gfm can parse it as an actual table.
    normalized = normalized.replace(/\|\s*\|/g, '|\n|');

    const rebuiltLines = normalized.split('\n').flatMap((line) => {
      const segments: string[] = [];
      let currentLine = line;

      const firstPipeIndex = currentLine.indexOf('|');
      if (firstPipeIndex > 0) {
        const prefix = currentLine.slice(0, firstPipeIndex).trimEnd();
        const candidateTableLine = currentLine.slice(firstPipeIndex).trimStart();

        if (prefix && candidateTableLine.startsWith('|')) {
          segments.push(prefix, '', candidateTableLine);
          currentLine = candidateTableLine;
        }
      }

      if (segments.length === 0) {
        segments.push(currentLine);
      }

      const lastSegment = segments[segments.length - 1] ?? '';
      const lastPipeIndex = lastSegment.lastIndexOf('|');
      if (lastSegment.startsWith('|') && lastPipeIndex >= 0 && lastPipeIndex < lastSegment.length - 1) {
        const tableLine = lastSegment.slice(0, lastPipeIndex + 1).trimEnd();
        const suffix = lastSegment.slice(lastPipeIndex + 1).trimStart();

        if (suffix) {
          segments.splice(segments.length - 1, 1, tableLine, '', suffix);
        }
      }

      return segments;
    });

    normalized = rebuiltLines.join('\n').replace(/\n{3,}/g, '\n\n');
  }

  return normalized;
}

/**
 * MessageBubble component
 * 
 * Renders an individual chat message with premium glassmorphism aesthetic,
 * Markdown support, and smooth Framer Motion animations.
 */
export const MessageBubble = memo(function MessageBubble({ message, resolveText, trainerId, userPhoto, userName }: MessageBubbleProps) {
  const { t } = useTranslation();
  const isTrainer = message.sender === 'Trainer';
  const displayText = resolveText ? resolveText(message) : message.text;
  const hiddenFallback = displayText === 'Analyze these images and provide practical guidance.';
  const textToRender = hiddenFallback ? '' : normalizeMarkdownText(displayText);
  const isEmpty = !textToRender || textToRender.trim() === '';

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
        "flex flex-col max-w-full lg:max-w-[88%] xl:max-w-[82%] 2xl:max-w-[88%]",
        isTrainer ? "items-start" : "items-end"
      )} data-testid="chat-message-bubble">
        <span className="text-[10px] font-black uppercase tracking-widest text-zinc-600 mb-1.5 ml-1">
          {isTrainer ? (trainerId ?? 'AI Trainer') : (userName ?? t('common.athlete'))}
        </span>
        
        <div className={cn(
          "px-5 py-4 rounded-[24px] relative overflow-hidden",
          isTrainer 
            ? "bg-white/[0.03] backdrop-blur-2xl border border-white/5 rounded-bl-none text-zinc-200 message-bubble-trainer" 
            : "bg-gradient-to-br from-indigo-500 to-indigo-600 border border-white/10 rounded-br-none text-white shadow-xl shadow-indigo-500/10 message-bubble-user"
        )}>
          {isTrainer && (
            <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-indigo-500/5 to-transparent pointer-events-none" />
          )}
          
          <div className="prose prose-invert prose-sm max-w-none font-medium leading-relaxed selection:bg-white/20 markdown-content">
             {isEmpty && isTrainer ? (
               <div className="flex gap-1 py-2 px-1">
                 <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                 <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                 <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
               </div>
             ) : (
               <ReactMarkdown remarkPlugins={[remarkGfm]}>{textToRender}</ReactMarkdown>
             )}
          </div>
          {message.images && message.images.length > 0 && (
            <div className="mt-3 grid grid-cols-2 gap-2">
              {message.images.map((image, index) => (
                <img
                  key={`${image.base64.slice(0, 12)}-${index.toString()}`}
                  src={`data:${image.mimeType};base64,${image.base64}`}
                  alt={`attachment-${index.toString()}`}
                  className="w-28 h-28 object-cover rounded-xl border border-white/10"
                />
              ))}
            </div>
          )}
        </div>
        
        <span className="text-[9px] font-bold text-zinc-700 mt-1.5 uppercase tracking-tighter">
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </motion.div>
  );
});
