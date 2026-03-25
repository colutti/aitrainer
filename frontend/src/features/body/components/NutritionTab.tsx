import { Flame, History, Plus, Beef, Wheat, Droplets } from 'lucide-react';
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

import { DataView } from '../../../shared/components/ui/premium/DataView';
import { Pagination } from '../../../shared/components/ui/premium/Pagination';
import { ViewHeader } from '../../../shared/components/ui/premium/ViewHeader';
import { Skeleton } from '../../../shared/components/ui/Skeleton';
import { useNutritionStore } from '../../../shared/hooks/useNutrition';
import { MacroCard } from '../../nutrition/components/MacroCard';
import { NutritionLogCard } from '../../nutrition/components/NutritionLogCard';

/**
 * NutritionTab component
 * 
 * Refactored to use DataView orchestrator and reusable UI components.
 */
export function NutritionTab() {
  const {
    logs,
    stats,
    isLoading,
    error,
    page,
    totalPages,
    fetchLogs,
    fetchStats,
    deleteLog,
  } = useNutritionStore();
  
  const { t } = useTranslation();
  const navigate = useNavigate();

  useEffect(() => {
    void fetchLogs();
    void fetchStats();
  }, [fetchLogs, fetchStats]);

  const today = stats?.today;
  const targetCals = stats?.daily_target ?? 2000;
  const macroTargets = stats?.macro_targets ?? { protein: 150, carbs: 200, fat: 60 };

  const calculatePercent = (current: number, target: number) => {
    if (!target) return 0;
    return Math.round((current / target) * 100);
  };

  const onRetry = () => {
    void fetchLogs();
    void fetchStats();
  };

  const onDelete = (id: string) => {
    void deleteLog(id);
  };

  const onPageChange = (p: number) => {
    void fetchLogs(p);
  };

  const loadingSkeleton = (
    <div className="space-y-8 animate-pulse">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-32 rounded-3xl bg-white/5" />)}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-10">
        {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-32 rounded-3xl bg-white/5" />)}
      </div>
    </div>
  );

  return (
    <div className="space-y-10">
      {/* MACROS OVERVIEW - Standardized with success data */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MacroCard 
          label={t('nutrition.calories')} 
          value={today?.calories ?? 0} 
          percent={calculatePercent(today?.calories ?? 0, targetCals)}
          unit="kcal" 
          color="primary" 
          icon={<Flame size={18} />} 
        />
        <MacroCard 
          label={t('nutrition.proteins')} 
          value={today?.protein_grams ?? 0} 
          percent={calculatePercent(today?.protein_grams ?? 0, macroTargets.protein)}
          unit="g" 
          color="red" 
          icon={<Beef size={18} />}
        />
        <MacroCard 
          label={t('nutrition.carbs')} 
          value={today?.carbs_grams ?? 0} 
          percent={calculatePercent(today?.carbs_grams ?? 0, macroTargets.carbs)}
          unit="g" 
          color="blue" 
          icon={<Wheat size={18} />}
        />
        <MacroCard 
          label={t('nutrition.fats')} 
          value={today?.fat_grams ?? 0} 
          percent={calculatePercent(today?.fat_grams ?? 0, macroTargets.fat)}
          unit="g" 
          color="green" 
          icon={<Droplets size={18} />}
        />
      </div>

      {/* HEADER SECTION */}
      <ViewHeader 
        title={t('nutrition.history_title')}
        subtitle={t('body.nutrition_subtitle')}
        icon={<History size={20} className="text-zinc-500" />}
        action={{
          label: t('nutrition.register_meal'),
          icon: <Plus size={20} strokeWidth={3} />,
          onClick: () => { void navigate('/dashboard/chat'); }
        }}
        className="px-2"
      />

      {/* DATA ORCHESTRATION LAYER */}
      <DataView 
        isLoading={isLoading && logs.length === 0}
        error={error}
        isEmpty={logs.length === 0}
        onRetry={onRetry}
        loadingSkeleton={loadingSkeleton}
        emptyState={{
          title: t('nutrition.empty_history_title'),
          icon: <History size={40} className="text-zinc-500" />
        }}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {logs.map(log => (
            <NutritionLogCard 
              key={log.id} 
              log={log} 
              onDelete={onDelete} 
            />
          ))}
        </div>

        <Pagination 
          currentPage={page}
          totalPages={totalPages}
          onPageChange={onPageChange}
          isLoading={isLoading}
        />
      </DataView>
    </div>
  );
}
