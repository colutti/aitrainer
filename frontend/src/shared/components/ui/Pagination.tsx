import { ChevronLeft, ChevronRight } from 'lucide-react';

import { Button } from './Button';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
  variant?: 'default' | 'premium';
}

/**
 * Pagination component
 * 
 * Standardized pagination controls with Previous/Next buttons and page indicator.
 */
export function Pagination({ 
  currentPage, 
  totalPages, 
  onPageChange, 
  isLoading = false,
  variant = 'default',
}: PaginationProps) {
  if (totalPages <= 1) return null;

  if (variant === 'premium') {
    return (
      <div className="flex justify-center items-center gap-4 mt-12">
        <Button
          variant="ghost"
          size="icon"
          disabled={currentPage === 1 || isLoading}
          onClick={() => { onPageChange(currentPage - 1); }}
          className="h-14 w-14 rounded-2xl bg-white/5 border border-white/5 text-zinc-400 hover:text-white hover:bg-white/10 disabled:opacity-20"
          aria-label="Anterior"
        >
          <ChevronLeft size={20} />
        </Button>

        <div className="flex flex-col items-center">
          <span className="text-zinc-500 font-black text-[10px] uppercase tracking-[0.2em] mb-0.5">Página</span>
          <span className="text-white font-black text-sm">
            {currentPage} <span className="text-zinc-600 mx-1">/</span> {totalPages}
          </span>
        </div>

        <Button
          variant="ghost"
          size="icon"
          disabled={currentPage === totalPages || isLoading}
          onClick={() => { onPageChange(currentPage + 1); }}
          className="h-14 w-14 rounded-2xl bg-white/5 border border-white/5 text-zinc-400 hover:text-white hover:bg-white/10 disabled:opacity-20"
          aria-label="Próxima"
        >
          <ChevronRight size={20} />
        </Button>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center gap-0.5 md:gap-2 pt-2 md:pt-4 px-1">
      <Button
        variant="secondary"
        size="sm"
        disabled={currentPage === 1 || isLoading}
        onClick={() => { onPageChange(currentPage - 1); }}
        className="gap-1 px-2 md:px-4"
        aria-label="Anterior"
      >
        <ChevronLeft size={14} className="md:w-4 md:h-4" />
        <span className="hidden sm:inline">Anterior</span>
      </Button>

      <div className="flex items-center px-1 md:px-4 font-medium text-text-secondary text-[10px] md:text-sm whitespace-nowrap">
        {currentPage}/{totalPages}
      </div>

      <Button
        variant="secondary"
        size="sm"
        disabled={currentPage === totalPages || isLoading}
        onClick={() => { onPageChange(currentPage + 1); }}
        className="gap-1 px-2 md:px-4"
        aria-label="Próxima"
      >
        <span className="hidden sm:inline">Próxima</span>
        <ChevronRight size={14} className="md:w-4 md:h-4" />
      </Button>
    </div>
  );
}
