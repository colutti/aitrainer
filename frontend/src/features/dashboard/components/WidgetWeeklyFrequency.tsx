import { Calendar } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { cn } from '../../../shared/utils/cn';

import { NoDataOverlay } from './NoDataOverlay';

interface WidgetWeeklyFrequencyProps {
  days?: boolean[] | null; // 7 booleans (Mon-Sun)
  className?: string;
}

export function WidgetWeeklyFrequency({ days, className }: WidgetWeeklyFrequencyProps) {
  const { t } = useTranslation();
  const isEmpty = !days || days.length === 0;

  // Use dummy days (all false) if empty
  const displayDays = (days && days.length > 0) ? days : [false, false, false, false, false, false, false];

  const dayLabels = t('dashboard.weekly_days', { returnObjects: true }) as string[];

  return (
    <div className={cn("relative group transition-all duration-500 flex flex-col h-full", className)}>
      <div className="flex items-center gap-3 mb-4">
        <div className="h-8 w-8 rounded-lg bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
          <Calendar size={16} />
        </div>
        <div>
          <h4 className="text-sm font-bold text-text-primary">{t('dashboard.frequency_title')}</h4>
          <p className="text-[10px] text-text-muted uppercase font-bold tracking-wider">{t('dashboard.frequency_subtitle')}</p>
        </div>
      </div>

      <div className={cn("flex justify-between items-center gap-2 px-1 transition-all duration-700", isEmpty && "blur-sm grayscale opacity-30 select-none")}>
        {displayDays.map((active, index) => (
          <div key={index} className="flex flex-col items-center gap-1.5 min-w-0">
            <div 
              className={cn(
                "w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center text-[9px] sm:text-[10px] font-bold transition-all duration-500 border relative",
                active 
                  ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.2)] scale-110" 
                  : "bg-white/5 text-text-muted border-white/5 opacity-50"
              )}
            >
              {dayLabels[index]}
              {active && (
                <div className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
              )}
            </div>
          </div>
        ))}
      </div>
      {isEmpty && <NoDataOverlay message={t('dashboard.no_workouts_yet')} />}
    </div>
  );
}
