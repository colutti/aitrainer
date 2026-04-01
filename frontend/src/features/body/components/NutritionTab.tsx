import { Flame, History, Plus, Beef, Wheat, Droplets } from 'lucide-react';
import { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

import { Button } from '../../../shared/components/ui/Button';
import { DataList } from '../../../shared/components/ui/DataList';
import { useDemoMode } from '../../../shared/hooks/useDemoMode';
import { useNutritionStore } from '../../../shared/hooks/useNutrition';
import { PREMIUM_UI } from '../../../shared/styles/ui-variants';
import { type NutritionLog, type NutritionFormData } from '../../../shared/types/nutrition';
import { cn } from '../../../shared/utils/cn';
import { MacroCard } from '../../nutrition/components/MacroCard';
import { NutritionLogCard } from '../../nutrition/components/NutritionLogCard';

import { NutritionLogDrawer } from './NutritionLogDrawer';

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
    page,
    totalPages,
    fetchLogs,
    fetchStats,
    deleteLog,
    createLog,
  } = useNutritionStore();
  
  const { t } = useTranslation();
  const { isReadOnly, blockIfReadOnly } = useDemoMode();
  const navigate = useNavigate();

  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [selectedLog, setSelectedLog] = useState<NutritionLog | null>(null);
  const [drawerMode, setDrawerMode] = useState<'view' | 'edit'>('view');

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

  const handleOpenDrawer = useCallback((log: NutritionLog | null, mode: 'view' | 'edit') => {
    setSelectedLog(log);
    setDrawerMode(mode);
    setIsDrawerOpen(true);
  }, []);

  const handleCloseDrawer = useCallback(() => {
    setIsDrawerOpen(false);
    setSelectedLog(null);
  }, []);

  const onSave = async (data: NutritionFormData) => {
    if (blockIfReadOnly()) return;
    
    try {
      await createLog({
        date: data.date,
        source: data.source,
        calories: data.calories,
        protein_grams: data.protein_grams ?? 0,
        carbs_grams: data.carbs_grams ?? 0,
        fat_grams: data.fat_grams ?? 0,
      });
      handleCloseDrawer();
    } catch {
      // Handled by store
    }
  };

  const onDelete = (id: string) => {
    if (blockIfReadOnly()) {
      return;
    }
    void deleteLog(id);
  };

  const onPageChange = (p: number) => {
    void fetchLogs(p);
  };

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

      {/* DATA ORCHESTRATION LAYER */}
      <DataList
        data={logs}
        actions={(
          <div className="flex gap-3">
             <Button
                type="button"
                variant="secondary"
                onClick={() => { if (!blockIfReadOnly()) void navigate('/dashboard/chat'); }}
                disabled={isReadOnly}
                className="px-5 rounded-full bg-white/5 border-white/10"
              >
                <Plus size={20} />
                <span className="hidden sm:inline">{t('nutrition.register_meal')} (AI)</span>
              </Button>
              <Button
                type="button"
                onClick={() => { handleOpenDrawer(null, 'edit'); }}
                disabled={isReadOnly}
                className={cn(PREMIUM_UI.button.premium, "px-5")}
              >
                <Plus size={20} strokeWidth={3} />
                {t('common.add')}
              </Button>
          </div>
        )}
        renderItem={(log) => (
          <NutritionLogCard
            log={log}
            isReadOnly={isReadOnly}
            onDelete={onDelete}
            onEdit={(l) => { handleOpenDrawer(l, 'edit'); }}
            onClick={(l) => { handleOpenDrawer(l, 'view'); }}
          />
        )}
        keyExtractor={(log) => log.id}
        isLoading={isLoading}
        layout="grid"
        emptyState={{
          title: t('nutrition.empty_history_title'),
          description: '',
          icon: <History size={40} className="text-zinc-500" />
        }}
        pagination={{
          currentPage: page,
          totalPages,
          onPageChange,
        }}
        className="space-y-8"
        gridClassName="grid-cols-1 md:grid-cols-2"
      />

      <NutritionLogDrawer
        log={selectedLog}
        isOpen={isDrawerOpen}
        onClose={handleCloseDrawer}
        onSubmit={onSave}
        mode={drawerMode}
        isReadOnly={isReadOnly}
      />
    </div>
  );
}
