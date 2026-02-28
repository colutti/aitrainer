import { 
  Database, 
  Trash2, 
  ChevronLeft, 
  ChevronRight, 
  Brain, 
  Calendar,
  Search,
  AlertCircle
} from 'lucide-react';
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../shared/components/ui/Button';
import { useConfirmation } from '../../shared/hooks/useConfirmation';
import { useMemoryStore } from '../../shared/hooks/useMemory';
import { useNotificationStore } from '../../shared/hooks/useNotification';
import { cn } from '../../shared/utils/cn';

/**
 * MemoriesPage component
 * 
 * Interface to manage "memories" - pieces of information the AI trainer
 * has learned about the user over time to provide better context.
 */
export function MemoriesPage() {
  const { 
    memories, 
    isLoading, 
    currentPage, 
    totalPages, 
    totalMemories,
    fetchMemories, 
    nextPage, 
    previousPage, 
    deleteMemory 
  } = useMemoryStore();

  const { confirm } = useConfirmation();
  const notify = useNotificationStore();
  const { t, i18n } = useTranslation();

  useEffect(() => {
    void fetchMemories();
  }, [fetchMemories]);

  const handleDelete = async (memoryId: string) => {
    const isConfirmed = await confirm({
      title: t('memories.delete_confirm_title'),
      message: t('memories.delete_confirm_message'),
      confirmText: t('memories.delete_confirm_btn'),
      type: 'danger'
    });

    if (isConfirmed) {
      try {
        await deleteMemory(memoryId);
        notify.success(t('memories.delete_success'));
      } catch {
        notify.error(t('memories.delete_error'));
      }
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-20">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
            <Brain className="text-gradient-start" size={32} />
            {t('memories.title')}
          </h1>
          <p className="text-text-secondary mt-1">{t('memories.subtitle')}</p>
        </div>
        
        <div className="bg-dark-card border border-border rounded-2xl px-6 py-3 flex items-center gap-4 shadow-sm">
          <div className="text-center md:text-left">
            <p className="text-[10px] uppercase font-bold text-text-muted tracking-widest">{t('memories.total_insights')}</p>
            <p className="text-2xl font-bold text-gradient-start">{totalMemories}</p>
          </div>
          <div className="w-px h-8 bg-border" />
          <Database size={24} className="text-text-muted opacity-50" />
        </div>
      </div>

      {/* Intro Info */}
      <div className="bg-gradient-start/5 border border-gradient-start/20 rounded-2xl p-6 flex items-start gap-4">
        <Database className="text-gradient-start mt-1 flex-shrink-0" size={24} />
        <div className="space-y-2">
          <h3 className="font-bold text-text-primary">{t('memories.what_are_memories')}</h3>
          <p className="text-sm text-text-secondary leading-relaxed">
            {t('memories.description')}
          </p>
        </div>
      </div>

      {/* Grid of Memories */}
      <div className="grid grid-cols-1 gap-4">
        {isLoading && memories.length === 0 ? (
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-24 bg-dark-card border border-border rounded-2xl animate-pulse" />
          ))
        ) : memories.length === 0 ? (
          <div className="py-20 flex flex-col items-center justify-center opacity-40">
            <Search size={64} className="mb-4 text-text-muted" />
            <p className="text-sm">{t('memories.empty_title')}</p>
          </div>
        ) : (
          memories.map((m) => (
            <div 
              key={m.id}
              className="bg-dark-card border border-border rounded-2xl p-5 hover:border-gradient-start/30 transition-all group relative overflow-hidden"
            >
              <div className="flex gap-4">
                <div className="flex-shrink-0 mt-1">
                  <div className="w-8 h-8 rounded-lg bg-dark-bg border border-border flex items-center justify-center text-gradient-start group-hover:bg-gradient-start group-hover:text-white transition-colors duration-300">
                    <Database size={16} />
                  </div>
                </div>
                
                <div className="flex-1 space-y-2">
                  <p className="text-text-primary text-sm leading-relaxed">{m.memory}</p>
                  <div className="flex items-center gap-4 text-[10px] text-text-muted font-bold uppercase tracking-wider">
                    <span className="flex items-center gap-1">
                      <Calendar size={12} />
                      {m.created_at ? new Date(m.created_at).toLocaleDateString(i18n.language) : 'N/A'}
                    </span>
                    <span className="px-2 py-0.5 bg-dark-bg rounded-md border border-border/50">{t('memories.ai_memory')}</span>
                  </div>
                </div>

                <div className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    onClick={() => {
                      void handleDelete(m.id);
                    }}
                    className="text-text-muted hover:text-red-500 hover:bg-red-500/10"
                  >
                    <Trash2 size={18} />
                  </Button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 pt-4">
          <Button
            variant="ghost"
            onClick={() => {
              void previousPage();
            }}
            disabled={currentPage === 1 || isLoading}
            className="gap-2"
          >
            <ChevronLeft size={20} />
            {t('memories.previous')}
          </Button>
          
          <div className="flex gap-1">
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                onClick={() => {
                  void fetchMemories(p);
                }}
                className={cn(
                  "w-10 h-10 rounded-xl text-sm font-bold transition-all",
                  currentPage === p 
                    ? "bg-gradient-start text-white shadow-orange" 
                    : "text-text-secondary hover:bg-dark-card"
                )}
              >
                {p}
              </button>
            ))}
          </div>

          <Button
            variant="ghost"
            onClick={() => {
              void nextPage();
            }}
            disabled={currentPage === totalPages || isLoading}
            className="gap-2"
          >
            {t('memories.next')}
            <ChevronRight size={20} />
          </Button>
        </div>
      )}

      {/* Limitations Warning */}
      <div className="flex items-center gap-2 p-4 bg-orange-500/5 text-orange-500/70 text-[10px] font-bold uppercase tracking-widest border border-orange-500/10 rounded-2xl justify-center">
        <AlertCircle size={14} />
        {t('memories.processing_warning')}
      </div>
    </div>
  );
}
