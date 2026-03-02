import { Trophy, ArrowUpRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import type { PRRecord } from '../../../shared/types/dashboard';
import { cn } from '../../../shared/utils/cn';

import { NoDataOverlay } from './NoDataOverlay';

interface WidgetRecentPRsProps {
  prs?: PRRecord[] | null;
}

export function WidgetRecentPRs({ prs }: WidgetRecentPRsProps) {
  const { t, i18n } = useTranslation();
  const isEmpty = !prs || prs.length === 0;

  // Use dummy records if empty
  const displayPrs: PRRecord[] = (prs && prs.length > 0) ? prs : [
    { id: '1', exercise: 'Supino Reto', weight: 80, reps: 5, date: new Date().toISOString() },
    { id: '2', exercise: 'Agachamento', weight: 100, reps: 8, date: new Date().toISOString() },
  ];

  return (
    <div className={cn("relative group transition-all duration-500 h-full flex flex-col", isEmpty && "min-h-[300px]")}>
      <div className="flex items-center gap-3 mb-6">
        <div className="h-8 w-8 rounded-lg bg-yellow-500/10 text-yellow-500 flex items-center justify-center">
          <Trophy size={16} />
        </div>
        <div>
          <h4 className="text-sm font-bold text-text-primary">{t('dashboard.recent_prs_title')}</h4>
          <p className="text-[10px] text-text-muted uppercase font-bold tracking-wider">{t('dashboard.recent_prs_subtitle') || "Novas Conquistas"}</p>
        </div>
      </div>
      
      <div className="relative flex-1">
        <div className={cn("grid gap-3 transition-all duration-700", isEmpty && "blur-sm grayscale opacity-30 select-none")}>
          {displayPrs.map((pr) => (
            <div 
              key={pr.id} 
              className="flex items-center justify-between p-4 bg-white/5 border border-white/5 rounded-2xl hover:border-yellow-500/30 transition-colors group relative overflow-hidden"
            >
              <div className="flex items-center gap-4 relative z-10">
                <div className="h-10 w-10 rounded-full bg-yellow-500/10 flex items-center justify-center text-yellow-500 font-bold text-xs">
                  {t('dashboard.pr_label')}
                </div>
                <div className="min-w-0">
                  <h4 className="font-bold text-text-primary group-hover:text-yellow-400 transition-colors truncate">{pr.exercise}</h4>
                  <p className="text-[10px] text-text-secondary">
                    {new Date(pr.date).toLocaleDateString(i18n.language, { day: '2-digit', month: 'short' })} • {t('dashboard.reps', { count: pr.reps })}
                  </p>
                </div>
              </div>

              <div className="text-right relative z-10 shrink-0">
                <div className="flex items-center gap-1 justify-end">
                  <span className="text-xl font-black text-white tracking-tight">{pr.weight}<span className="text-sm font-medium text-text-muted ml-0.5">{t('dashboard.weight_unit')}</span></span>
                </div>
                {pr.previous_weight && (
                  <div className="flex items-center justify-end gap-1 text-[10px] text-emerald-400 font-bold">
                      <ArrowUpRight size={10} />
                      <span>+{((pr.weight - pr.previous_weight)).toFixed(1)}{t('dashboard.weight_unit')}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
        {isEmpty && <NoDataOverlay message={t('dashboard.no_prs_yet')} />}
      </div>
    </div>
  );
}
