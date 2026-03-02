import { useTranslation } from 'react-i18next';

import { cn } from '../../../shared/utils/cn';

interface NoDataOverlayProps {
  message?: string;
  className?: string;
}

export function NoDataOverlay({ message, className }: NoDataOverlayProps) {
  const { t } = useTranslation();
  return (
    <div className={cn(
      "absolute inset-0 z-20 flex items-center justify-center backdrop-blur-[2px] bg-dark-bg/40 rounded-2xl transition-all duration-500",
      className
    )}>
      <div className="bg-dark-card/80 border border-white/10 px-4 py-2 rounded-full shadow-2xl backdrop-blur-md animate-in fade-in zoom-in duration-300">
        <p className="text-xs font-bold text-text-primary tracking-wide uppercase">
          {message ?? t('dashboard.no_data_yet')}
        </p>
      </div>
    </div>
  );
}
