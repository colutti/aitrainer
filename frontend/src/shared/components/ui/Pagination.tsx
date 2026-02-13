import { ChevronLeft, ChevronRight } from 'lucide-react';

import { Button } from './Button';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
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
  isLoading = false 
}: PaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-center gap-0.5 md:gap-2 pt-2 md:pt-4 px-1">
      <Button
        variant="secondary"
        size="sm"
        disabled={currentPage === 1 || isLoading}
        onClick={() => { onPageChange(currentPage - 1); }}
        className="gap-1 px-2 md:px-4"
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
      >
        <span className="hidden sm:inline">Próxima</span>
        <ChevronRight size={14} className="md:w-4 md:h-4" />
      </Button>
    </div>
  );
}
