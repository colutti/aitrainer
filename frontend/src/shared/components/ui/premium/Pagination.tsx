import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
}

/**
 * Standardized Pagination component for the Premium UI.
 */
export function Pagination({ currentPage, totalPages, onPageChange, isLoading }: PaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex justify-center items-center gap-4 mt-12">
      <button 
        disabled={currentPage === 1 || isLoading}
        onClick={() => { onPageChange(currentPage - 1); }}
        className="p-4 rounded-2xl bg-white/5 border border-white/5 text-zinc-400 hover:text-white disabled:opacity-20 transition-all active:scale-90"
      >
        <ChevronLeft size={20} />
      </button>
      
      <div className="flex flex-col items-center">
        <span className="text-zinc-500 font-black text-[10px] uppercase tracking-[0.2em] mb-0.5">Página</span>
        <span className="text-white font-black text-sm">
          {currentPage} <span className="text-zinc-600 mx-1">/</span> {totalPages}
        </span>
      </div>

      <button 
        disabled={currentPage === totalPages || isLoading}
        onClick={() => { onPageChange(currentPage + 1); }}
        className="p-4 rounded-2xl bg-white/5 border border-white/5 text-zinc-400 hover:text-white disabled:opacity-20 transition-all active:scale-90"
      >
        <ChevronRight size={20} />
      </button>
    </div>
  );
}
