import { Bot, Info, Send, Sparkles, Trash2 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

import { Button } from '../../shared/components/ui/Button';
import { useChatStore } from '../../shared/hooks/useChat';
import { useConfirmation } from '../../shared/hooks/useConfirmation';
import { cn } from '../../shared/utils/cn';

import { MessageBubble } from './components/MessageBubble';

/**
 * ChatPage component
 * 
 * Interactive AI assistant interface for health, fitness and nutrition advice.
 * Supports real-time streaming and persistent history.
 */
export function ChatPage() {
  const { messages, isStreaming, error, fetchHistory, sendMessage, clearHistory } = useChatStore();
  const { confirm } = useConfirmation();
  
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    void fetchHistory();
  }, [fetchHistory]);

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e?: React.BaseSyntheticEvent) => {
    e?.preventDefault();
    if (!inputValue.trim() || isStreaming) return;

    const text = inputValue.trim();
    setInputValue('');
    await sendMessage(text);
  };

  const handleClear = async () => {
    const isConfirmed = await confirm({
      title: 'Limpar Conversa',
      message: 'Tem certeza que deseja apagar todo o histórico desta conversa?',
      confirmText: 'Limpar',
      type: 'danger'
    });

    if (isConfirmed) {
      clearHistory();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-160px)] md:h-[calc(100vh-120px)] animate-in fade-in duration-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-gradient-start to-gradient-end flex items-center justify-center text-white shadow-orange">
            <Bot size={28} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
              Treinador AI
              <Sparkles size={16} className="text-orange-400" />
            </h1>
            <p className="text-xs text-text-secondary">Seu mentor 24/7 para saúde e performance.</p>
          </div>
        </div>
        
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={() => {
            void handleClear();
          }}
          title="Limpar conversa"
          className="text-text-muted hover:text-red-500 hover:bg-red-500/10"
        >
          <Trash2 size={20} />
        </Button>
      </div>

      {/* Chat Container */}
      <div className="flex-1 min-h-0 bg-dark-card border border-border rounded-3xl flex flex-col shadow-xl overflow-hidden">
        {/* Help Banner */}
        {messages.length === 0 && (
          <div className="p-4 bg-gradient-start/5 border-b border-border/50 flex gap-3 animate-in slide-in-from-top-2">
            <Info className="text-gradient-start flex-shrink-0" size={20} />
            <p className="text-xs text-text-secondary leading-relaxed">
              Dica: Você pode perguntar sobre seus últimos treinos, pedir sugestões de refeições baseadas nos seus macros ou tirar dúvidas sobre suplementação.
            </p>
          </div>
        )}

        {/* Messages List */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center opacity-40">
              <Bot size={64} className="mb-4 text-text-muted" />
              <p className="text-sm">Inicie uma conversa para receber orientações personalizadas.</p>
            </div>
          ) : (
            messages.map((msg, i) => (
              <MessageBubble key={`${msg.timestamp}-${i.toString()}`} message={msg} />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Status Indicators */}
        {error && (
          <div className="px-6 py-2 bg-red-500/10 text-red-500 text-xs text-center border-t border-red-500/20">
            {error}
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 md:p-6 bg-dark-bg/30 border-t border-border mt-auto">
          <form 
            onSubmit={(e) => {
              void handleSend(e);
            }} 
            className="relative flex items-center"
          >
            <input
              type="text"
              placeholder="Pergunte qualquer coisa..."
              className="w-full bg-dark-bg border border-border rounded-2xl py-4 pl-5 pr-14 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-gradient-start/50 focus:border-gradient-start/50 transition-all shadow-inner"
              value={inputValue}
              onChange={(e) => {
                setInputValue(e.target.value);
              }} 
              disabled={isStreaming}
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || isStreaming}
              className={cn(
                "absolute right-2 p-3 rounded-xl transition-all active:scale-95",
                inputValue.trim() && !isStreaming
                  ? "bg-gradient-start text-white shadow-orange"
                  : "bg-dark-bg/10 text-text-muted"
              )}
            >
              <Send size={20} className={cn(isStreaming && "animate-pulse")} />
            </button>
          </form>
          <p className="mt-4 text-[10px] text-center text-text-muted uppercase tracking-widest font-bold">
            Pode conter informações imprecisas. Consulte sempre um profissional de saúde.
          </p>
        </div>
      </div>
    </div>
  );
}
