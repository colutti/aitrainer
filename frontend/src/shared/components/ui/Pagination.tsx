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
    <div className="flex items-center justify-center gap-2 pt-4">
      <Button 
        variant="secondary" 
        disabled={currentPage === 1 || isLoading}
        onClick={() => { onPageChange(currentPage - 1); }}
        className="gap-1"
      >
        <ChevronLeft size={16} />
        Anterior
      </Button>
      
      <div className="flex items-center px-4 font-medium text-text-secondary">
        Página {currentPage} de {totalPages}
      </div>
      
      <Button 
        variant="secondary"
        disabled={currentPage === totalPages || isLoading}
        onClick={() => { onPageChange(currentPage + 1); }}
        className="gap-1"
      >
        Próxima
        <ChevronRight size={16} />
      </Button>
    </div>
  );
}
