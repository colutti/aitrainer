import { 
  Database, 
  Trash2, 
  ChevronLeft, 
  ChevronRight, 
  Brain, 
  Calendar,
  Search,
  AlertCircle,
  Sparkles
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { Skeleton } from '../../../shared/components/ui/Skeleton';
import { PREMIUM_UI } from '../../../shared/styles/ui-variants';
import { type Memory } from '../../../shared/types/memory';
import { cn } from '../../../shared/utils/cn';

export interface MemoriesViewProps {
  memories: Memory[];
  isLoading: boolean;
  totalMemories: number;
  currentPage: number;
  totalPages: number;
  isReadOnly?: boolean;
  onDelete: (id: string) => void;
  onPageChange: (page: number) => void;
}

export function MemoriesView({
  memories,
  isLoading,
  totalMemories,
  currentPage,
  totalPages,
  isReadOnly = false,
  onDelete,
  onPageChange,
}: MemoriesViewProps) {
  const { t, i18n } = useTranslation();
  const locale = i18n.language.toLowerCase();
  const localeKey = locale.startsWith('pt')
    ? 'pt-BR'
    : locale.startsWith('es')
      ? 'es-ES'
      : 'en-US';

  const getMemoryText = (memory: typeof memories[number]) => {
    const translations = memory.translations;
    const localeTranslation = translations?.[localeKey];
    if (localeTranslation) {
      return localeTranslation;
    }
    const fallbackTranslation = translations?.[locale] ?? translations?.[locale.slice(0, 2)];
    if (fallbackTranslation) {
      return fallbackTranslation;
    }
    return memory.memory;
  };

  if (isLoading && memories.length === 0) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="flex justify-between items-end">
           <Skeleton className="h-12 w-64 bg-white/5" />
           <Skeleton className="h-12 w-40 rounded-2xl bg-white/5" />
        </div>
        <div className="space-y-4">
           {[1, 2, 3, 4, 5].map(i => <Skeleton key={i} className="h-24 rounded-2xl bg-white/5" />)}
        </div>
      </div>
    );
  }

  return (
    <div className={cn(PREMIUM_UI.animation.fadeIn, "space-y-10 pb-20")}>
      {isReadOnly && (
        <PremiumCard className="p-4 border-amber-500/20 bg-amber-500/5 text-amber-200 text-[10px] font-black uppercase tracking-[0.2em]">
          Demo Read-Only
        </PremiumCard>
      )}
      
      {/* HEADER SECTION */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <p className={PREMIUM_UI.text.label}>{t('memories.subtitle')}</p>
          <h1 className={PREMIUM_UI.text.heading}>
            <Brain className="inline-block mr-3 text-indigo-400 mb-1" size={32} />
            {t('memories.title')}
          </h1>
        </div>
        
        <PremiumCard className="px-6 py-3 flex items-center gap-4 bg-indigo-500/5 border-indigo-500/20 ring-1 ring-indigo-500/10">
          <div className="text-left">
            <p className="text-[10px] uppercase font-black text-zinc-500 tracking-widest leading-none mb-1">{t('memories.total_insights')}</p>
            <p className="text-2xl font-black text-white leading-none">{totalMemories}</p>
          </div>
          <div className="w-px h-8 bg-white/10" />
          <Database size={24} className="text-indigo-400 opacity-50" />
        </PremiumCard>
      </div>

      {/* INTRO EXPLANATION */}
      <PremiumCard className="p-6 flex items-start gap-5 bg-gradient-to-br from-indigo-900/20 to-transparent border-indigo-500/20">
        <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0">
           <Sparkles size={24} />
        </div>
        <div className="space-y-1">
          <h3 className="font-black text-white uppercase tracking-tight">{t('memories.what_are_memories')}</h3>
          <p className="text-sm text-zinc-500 font-medium leading-relaxed">
            {t('memories.description')}
          </p>
        </div>
      </PremiumCard>

      {/* LIST OF MEMORIES */}
      <div className="space-y-4">
        {memories.length === 0 ? (
          <div className="py-20 flex flex-col items-center justify-center text-center opacity-30 select-none">
            <Search size={64} className="mb-4 text-zinc-600" />
            <p className="text-lg font-black text-white uppercase tracking-widest">{t('memories.empty_title')}</p>
          </div>
        ) : (
          memories.map((m) => (
            <PremiumCard 
              key={m.id}
              data-testid="memory-card"
              className="p-5 md:p-6 group hover:border-indigo-500/30"
            >
              <div className="flex gap-5 items-start">
                <div className="shrink-0 mt-1">
                  <div className="w-10 h-10 rounded-xl bg-zinc-900 border border-white/5 flex items-center justify-center text-indigo-400 group-hover:bg-indigo-500 group-hover:text-white transition-all duration-500 shadow-inner">
                    <Database size={18} />
                  </div>
                </div>
                
                <div className="flex-1 space-y-3 min-w-0">
                  <p className="text-white text-base font-medium leading-relaxed">{getMemoryText(m)}</p>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1.5 text-[10px] text-zinc-500 font-black uppercase tracking-widest">
                      <Calendar size={12} />
                      {m.created_at ? new Date(m.created_at).toLocaleDateString(i18n.language) : 'N/A'}
                    </div>
                    <span className="px-2 py-0.5 bg-white/5 rounded-md border border-white/5 text-[9px] font-black text-zinc-600 uppercase tracking-widest">
                       {t('memories.ai_memory')}
                    </span>
                  </div>
                </div>

                <Button
                  type="button"
                  variant="ghost"
                  onClick={(e) => { 
                    e.stopPropagation();
                    if (isReadOnly) return;
                    onDelete(m.id); 
                  }}
                  aria-label="shared.delete"
                  data-testid="btn-delete-memory"
                  disabled={isReadOnly}
                  className="shrink-0 h-10 w-10 rounded-full bg-red-500/5 text-red-500 md:opacity-0 group-hover:opacity-100 transition-all hover:bg-red-500/20 disabled:opacity-30 disabled:hover:bg-red-500/5"
                  title={t('shared.delete')}
                >
                  <Trash2 size={18} />
                </Button>
              </div>
            </PremiumCard>
          ))
        )}
      </div>

      {/* PAGINATION */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-6 pt-6 border-t border-white/5">
          <Button
            type="button"
            variant="ghost"
            onClick={() => { onPageChange(currentPage - 1); }}
            disabled={isReadOnly || currentPage === 1 || isLoading}
            className="flex items-center gap-2 px-6 py-2 rounded-full bg-white/5 border border-white/10 text-xs font-black uppercase tracking-widest text-zinc-400 hover:text-white hover:bg-white/10 disabled:opacity-20 transition-all"
          >
            <ChevronLeft size={16} />
            {t('memories.previous')}
          </Button>
          
          <span className="text-zinc-500 font-black text-xs uppercase tracking-widest">
            {currentPage} <span className="mx-1 opacity-30">/</span> {totalPages}
          </span>

          <Button
            type="button"
            variant="ghost"
            onClick={() => { onPageChange(currentPage + 1); }}
            disabled={isReadOnly || currentPage === totalPages || isLoading}
            className="flex items-center gap-2 px-6 py-2 rounded-full bg-white/5 border border-white/10 text-xs font-black uppercase tracking-widest text-zinc-400 hover:text-white hover:bg-white/10 disabled:opacity-20 transition-all"
          >
            {t('memories.next')}
            <ChevronRight size={16} />
          </Button>
        </div>
      )}

      {/* WARNING FOOTER */}
      <div className="flex items-center gap-2 p-4 bg-orange-500/5 text-orange-500/50 text-[9px] font-black uppercase tracking-[0.2em] border border-orange-500/10 rounded-2xl justify-center backdrop-blur-sm">
        <AlertCircle size={14} />
        {t('memories.processing_warning')}
      </div>
    </div>
  );
}
