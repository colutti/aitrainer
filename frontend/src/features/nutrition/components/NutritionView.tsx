import { 
  Flame, 
  Plus, 
  Upload, 
  Beef,
  Wheat,
  Droplets,
  AlertCircle
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { DataList } from '../../../shared/components/ui/DataList';
import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { Skeleton } from '../../../shared/components/ui/Skeleton';
import { PREMIUM_UI } from '../../../shared/styles/ui-variants';
import { type NutritionLog, type NutritionStats } from '../../../shared/types/nutrition';
import { cn } from '../../../shared/utils/cn';
import { formatNumber } from '../../../shared/utils/format-number';

import { NutritionLogCard } from './NutritionLogCard';

export interface NutritionViewProps {
  logs: NutritionLog[];
  stats: NutritionStats | null;
  isLoading: boolean;
  isReadOnly?: boolean;
  onRegisterMeal: () => void;
  onImport: () => void;
  onDeleteLog: (id: string) => void;
  pagination: {
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
  };
}

export function NutritionView({
  logs,
  stats,
  isLoading,
  isReadOnly = false,
  onRegisterMeal,
  onImport,
  onDeleteLog,
  pagination,
}: NutritionViewProps) {
  const { t } = useTranslation();

  const today = stats?.today;
  const targetCals = stats?.daily_target ?? 2500;
  const macroTargets = stats?.macro_targets ?? { protein: 180, carbs: 250, fat: 80 };

  const targetCalsStr = String(targetCals);
  const proteinTargetStr = String(macroTargets.protein);
  const carbsTargetStr = String(macroTargets.carbs);
  const fatTargetStr = String(macroTargets.fat);
  const stabilityScoreStr = String(stats?.stability_score ?? 0);

  if (isLoading && logs.length === 0) {
    return (
      <div data-testid="nutrition-skeleton" className="space-y-8 animate-pulse">
        <div className="flex justify-between items-end">
          <Skeleton className="h-12 w-64 bg-white/5" />
          <div className="flex gap-3">
            <Skeleton className="h-12 w-32 rounded-full bg-white/5" />
            <Skeleton className="h-12 w-40 rounded-full bg-white/5" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-32 rounded-[32px] bg-white/5" />)}
        </div>
      </div>
    );
  }

  return (
    <div className={cn(PREMIUM_UI.animation.fadeIn, "space-y-8 pb-20")}>
      
      {/* HEADER */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className={PREMIUM_UI.text.heading}>{t('nutrition.title')}</h1>
          <p className={PREMIUM_UI.text.label}>{t('nutrition.subtitle')}</p>
        </div>
        
        <div className="flex gap-3">
          <Button
            type="button"
            variant="secondary"
            onClick={onImport}
            disabled={isReadOnly}
            className="flex items-center gap-2 px-5 py-3 rounded-full bg-white/5 border border-white/10 text-white font-bold hover:bg-white/10 transition-all"
          >
            <Upload size={18} />
            <span className="hidden sm:inline">{t('nutrition.import')}</span>
          </Button>
          <Button
            type="button"
            onClick={onRegisterMeal}
            disabled={isReadOnly}
            className="flex items-center gap-2 px-6 py-3 rounded-full bg-white text-black font-black hover:scale-105 active:scale-95 transition-all shadow-xl shadow-white/10"
          >
            <Plus size={20} strokeWidth={3} />
            {t('nutrition.register_meal')}
          </Button>
        </div>
      </div>

      {/* TODAY SUMMARY BENTO */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Calories Card */}
        <PremiumCard className="col-span-2 md:col-span-1 p-6 flex flex-col justify-between min-h-[160px] bg-gradient-to-br from-orange-500/10 to-transparent">
           <div className="flex items-center gap-2 text-orange-400">
              <Flame size={18} fill="currentColor" />
              <span className="text-[10px] font-black uppercase tracking-widest">{t('nutrition.calories')}</span>
           </div>
           <div>
              <p className="text-4xl font-black text-white leading-none">
                {formatNumber(today?.calories ?? 0, 'integer')}
              </p>
              <p className="text-xs font-bold text-zinc-500 mt-1">/ {targetCalsStr} kcal</p>
           </div>
           <div className="mt-4 h-1.5 w-full bg-black/40 rounded-full overflow-hidden">
              <div 
                className="h-full bg-orange-500 rounded-full shadow-[0_0_10px_rgba(249,115,22,0.5)]" 
                style={{ width: `${String(Math.min(100, ((today?.calories ?? 0) / targetCals) * 100))}%` }}
              />
           </div>
        </PremiumCard>

        {/* Proteins */}
        <PremiumCard className="p-6 flex flex-col justify-between min-h-[160px]">
           <div className="flex items-center gap-2 text-red-400">
              <Beef size={18} />
              <span className="text-[10px] font-black uppercase tracking-widest">{t('nutrition.proteins')}</span>
           </div>
           <div>
              <p className="text-3xl font-black text-white leading-none">{String(today?.protein_grams ?? 0)}g</p>
              <p className="text-xs font-bold text-zinc-500 mt-1">/ {proteinTargetStr}g</p>
           </div>
           <div className="mt-4 h-1.5 w-full bg-black/40 rounded-full overflow-hidden">
              <div 
                className="h-full bg-red-500 rounded-full" 
                style={{ width: `${String(Math.min(100, ((today?.protein_grams ?? 0) / macroTargets.protein) * 100))}%` }}
              />
           </div>
        </PremiumCard>

        {/* Carbs */}
        <PremiumCard className="p-6 flex flex-col justify-between min-h-[160px]">
           <div className="flex items-center gap-2 text-blue-400">
              <Wheat size={18} />
              <span className="text-[10px] font-black uppercase tracking-widest">{t('nutrition.carbs')}</span>
           </div>
           <div>
              <p className="text-3xl font-black text-white leading-none">{String(today?.carbs_grams ?? 0)}g</p>
              <p className="text-xs font-bold text-zinc-500 mt-1">/ {carbsTargetStr}g</p>
           </div>
           <div className="mt-4 h-1.5 w-full bg-black/40 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-500 rounded-full" 
                style={{ width: `${String(Math.min(100, ((today?.carbs_grams ?? 0) / macroTargets.carbs) * 100))}%` }}
              />
           </div>
        </PremiumCard>

        {/* Fats */}
        <PremiumCard className="p-6 flex flex-col justify-between min-h-[160px]">
           <div className="flex items-center gap-2 text-emerald-400">
              <Droplets size={18} />
              <span className="text-[10px] font-black uppercase tracking-widest">{t('nutrition.fats')}</span>
           </div>
           <div>
              <p className="text-3xl font-black text-white leading-none">{String(today?.fat_grams ?? 0)}g</p>
              <p className="text-xs font-bold text-zinc-500 mt-1">/ {fatTargetStr}g</p>
           </div>
           <div className="mt-4 h-1.5 w-full bg-black/40 rounded-full overflow-hidden">
              <div 
                className="h-full bg-emerald-500 rounded-full" 
                style={{ width: `${String(Math.min(100, ((today?.fat_grams ?? 0) / macroTargets.fat) * 100))}%` }}
              />
           </div>
        </PremiumCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* History Column */}
        <div className="lg:col-span-2 space-y-4">
           <div className="flex items-center justify-between px-2">
              <h2 className="text-xl font-black text-white tracking-tight uppercase">{t('nutrition.history_title')}</h2>
              <Button type="button" variant="ghost" size="sm" className="h-auto p-0 text-[10px] font-black text-zinc-500 uppercase tracking-widest hover:text-white hover:bg-transparent transition-colors">
                 {t('nutrition.view_charts')}
              </Button>
           </div>
           
           <DataList
             data={logs}
             renderItem={(log) => (
               <NutritionLogCard log={log} isReadOnly={isReadOnly} onDelete={onDeleteLog} />
             )}
             keyExtractor={(log) => log.id}
             isLoading={isLoading}
             layout="grid"
             emptyState={{
               title: t('nutrition.empty_history_title'),
               description: '',
             }}
             pagination={{
               currentPage: pagination.currentPage,
               totalPages: pagination.totalPages,
               onPageChange: pagination.onPageChange,
             }}
             className="space-y-8"
             gridClassName="grid-cols-1 md:grid-cols-2"
           />
        </div>

        {/* Adherence Sidebar */}
        <div className="space-y-4">
           <h2 className="text-xl font-black text-white tracking-tight uppercase px-2">{t('nutrition.adherence_title')}</h2>
           <PremiumCard className="p-8 flex flex-col items-center text-center">
              <div className="relative w-32 h-32 flex items-center justify-center mb-6">
                <svg className="w-full h-full transform -rotate-90 drop-shadow-[0_0_15px_rgba(99,102,241,0.2)]">
                  <circle cx="64" cy="64" r="58" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-white/5" />
                  <circle
                    cx="64" cy="64" r="58" stroke="currentColor" strokeWidth="8" fill="transparent"
                    strokeDasharray={364.4}
                    strokeDashoffset={364.4 * (1 - (stats?.stability_score ?? 0) / 100)}
                    className="text-indigo-500"
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  { }
                  <span className="text-4xl font-black text-white">{stabilityScoreStr}%</span>
                  <span className="text-[9px] text-zinc-500 font-bold uppercase tracking-widest mt-1">{t('nutrition.consistency')}</span>
                </div>
              </div>
              
              <h3 className="font-bold text-white mb-2">{t('nutrition.stability_score')}</h3>
              <p className="text-xs text-zinc-500 font-medium leading-relaxed">
                {t('nutrition.stability_description')}
              </p>

              <div className="mt-8 pt-6 border-t border-white/5 w-full grid grid-cols-7 gap-1.5">
                {stats?.weekly_adherence.map((adhered, i) => {
                  const weeklyDays = t('nutrition.weekly_days', { returnObjects: true }) as string[];
                  return (
                    <div key={i} className="flex flex-col items-center gap-2">
                      <div className={cn(
                        "w-full aspect-square rounded-md border transition-all",
                        adhered 
                          ? "bg-indigo-500 border-indigo-400 shadow-[0_0_10px_rgba(99,102,241,0.3)]" 
                          : "bg-white/5 border-white/10"
                      )} />
                      <span className="text-[10px] text-zinc-600 font-black uppercase">{weeklyDays[i]}</span>
                    </div>
                  );
                })}
              </div>
           </PremiumCard>
        </div>
      </div>

      {/* WARNING FOOTER */}
      <div className="flex items-center gap-2 p-4 bg-orange-500/5 text-orange-500/50 text-[9px] font-black uppercase tracking-[0.2em] border border-orange-500/10 rounded-2xl justify-center backdrop-blur-sm">
        <AlertCircle size={14} />
        {t('memories.processing_warning')}
      </div>
    </div>
  );
}
