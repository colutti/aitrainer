import { AlertCircle, RefreshCcw, FolderOpen } from 'lucide-react';
import { type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

import { PREMIUM_UI } from '../../../styles/ui-variants';
import { cn } from '../../../utils/cn';
import { Button } from '../Button';

interface DataViewProps {
  isLoading: boolean;
  error: unknown;
  isEmpty: boolean;
  onRetry?: () => void;
  loadingSkeleton?: ReactNode;
  emptyState?: {
    title?: string;
    description?: string;
    icon?: ReactNode;
  };
  children: ReactNode;
}

/**
 * Standardized Data Orchestrator for Premium Views.
 * Handles Loading, Error, Empty, and Success states consistently.
 */
export function DataView({ 
  isLoading, 
  error, 
  isEmpty, 
  onRetry, 
  loadingSkeleton, 
  emptyState,
  children 
}: DataViewProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return <>{loadingSkeleton}</>;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center animate-in fade-in zoom-in duration-300">
        <div className="w-20 h-20 rounded-[2rem] bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-500 mb-6 shadow-2xl shadow-red-500/10">
          <AlertCircle size={40} />
        </div>
        <h3 className="text-2xl font-black text-white mb-2">{t('common.error_loading', 'Erro ao carregar')}</h3>
        <p className="text-zinc-500 max-w-xs mb-8 text-sm">{t('common.error_loading_desc', 'Não foi possível carregar os dados.')}</p>
        {onRetry && (
          <Button
            type="button"
            variant="secondary"
            onClick={onRetry}
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-white/5 border border-white/10 text-white font-bold hover:bg-white/10 transition-all active:scale-95"
          >
            <RefreshCcw size={18} />
            {t('common.retry', 'Tentar novamente')}
          </Button>
        )}
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center opacity-40 animate-in fade-in duration-500 border-2 border-dashed border-white/5 rounded-[32px]">
        <div className="w-20 h-20 rounded-3xl bg-white/5 flex items-center justify-center mb-6">
          {emptyState?.icon ?? <FolderOpen size={40} className="text-zinc-500" />}
        </div>
        <h3 className="text-xl font-bold text-white mb-2">{emptyState?.title ?? t('common.no_data', 'Nenhum dado')}</h3>
        <p className="text-sm text-zinc-500 max-w-xs">{emptyState?.description ?? t('common.no_data_desc', 'Sem registros por enquanto.')}</p>
      </div>
    );
  }

  return <div className={cn(PREMIUM_UI.animation.fadeIn)}>{children}</div>;
}
