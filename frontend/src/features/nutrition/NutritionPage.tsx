import { 
  Beef, 
  ChevronRight,
  Droplets,
  Flame, 
  Plus, 
  TrendingDown,
  Upload, 
  Utensils, 
  Wheat
} from 'lucide-react';
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../shared/components/ui/Button';
import { DataList } from '../../shared/components/ui/DataList';
import { useConfirmation } from '../../shared/hooks/useConfirmation';
import { useNotificationStore } from '../../shared/hooks/useNotification';
import { useNutritionStore } from '../../shared/hooks/useNutrition';
import { cn } from '../../shared/utils/cn';

import { MacroCard } from './components/MacroCard';
import { NutritionLogCard } from './components/NutritionLogCard';

/**
 * NutritionPage component
 * 
 * Main interface for tracking and analyzing nutritional intake.
 * Displays daily progress, historical logs, and allows data import.
 */
export function NutritionPage() {
  const { 
    logs, 
    stats, 
    isLoading, 
    fetchLogs, 
    fetchStats, 
    deleteLog,
    page,
    totalPages
  } = useNutritionStore();
  
  const { confirm } = useConfirmation();
  const notify = useNotificationStore();
  const { t } = useTranslation();

  useEffect(() => {
    void fetchLogs();
    void fetchStats();
  }, [fetchLogs, fetchStats]);

  const handleDelete = async (id: string) => {
    const isConfirmed = await confirm({
      title: t('nutrition.delete_confirm_title'),
      message: t('nutrition.delete_confirm_message'),
      confirmText: t('nutrition.delete_confirm_btn'),
      type: 'danger',
    });

    if (isConfirmed) {
      try {
        await deleteLog(id);
        notify.success(t('nutrition.delete_success'));
      } catch {
        notify.error(t('nutrition.delete_error'));
      }
    }
  };

  const today = stats?.today;
  const targets = stats?.daily_target ?? 2500;
  const macroTargets = stats?.macro_targets ?? { protein: 180, carbs: 250, fat: 80 };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
            <Utensils className="text-gradient-start" size={32} />
            {t('nutrition.title')}
          </h1>
          <p className="text-text-secondary mt-1">
            {t('nutrition.subtitle')}
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" size="lg" className="gap-2">
             <Upload size={20} />
             {t('nutrition.import')}
          </Button>
          <Button variant="primary" size="lg" className="shadow-orange gap-2">
            <Plus size={20} />
            {t('nutrition.register_meal')}
          </Button>
        </div>
      </div>

      {/* Daily Progress */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
          <Flame className="text-orange-500" size={20} />
          {t('nutrition.today_progress')}
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MacroCard
            label={t('nutrition.calories')}
            value={today?.calories ?? 0}
            unit="kcal"
            percent={((today?.calories ?? 0) / targets) * 100}
            color="primary"
            icon={<Flame size={20} />}
          />
          <MacroCard
            label={t('nutrition.proteins')}
            value={today?.protein_grams ?? 0}
            unit="g"
            percent={((today?.protein_grams ?? 0) / macroTargets.protein) * 100}
            color="red"
            icon={<Beef size={20} />}
          />
          <MacroCard
            label={t('nutrition.carbs')}
            value={today?.carbs_grams ?? 0}
            unit="g"
            percent={((today?.carbs_grams ?? 0) / macroTargets.carbs) * 100}
            color="blue"
            icon={<Wheat size={20} />}
          />
          <MacroCard
            label={t('nutrition.fats')}
            value={today?.fat_grams ?? 0}
            unit="g"
            percent={((today?.fat_grams ?? 0) / macroTargets.fat) * 100}
            color="green"
            icon={<Droplets size={20} />}
          />
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* History */}
        <div className="lg:col-span-2 space-y-4">
          <DataList
            title={t('nutrition.history_title')}
            data={logs}
            isLoading={isLoading}
            renderItem={(log) => (
              <NutritionLogCard 
                log={log} 
                onDelete={(id) => {
                  void handleDelete(id);
                }}
              />
            )}
            keyExtractor={(item) => item.id}
            layout="list"
            emptyState={{
              title: t('nutrition.empty_history_title'),
              description: t('nutrition.empty_history_desc')
            }}
            pagination={{
              currentPage: page,
              totalPages: totalPages,
              onPageChange: (newPage) => { void fetchLogs(newPage); }
            }}
            actions={
              <Button variant="ghost" size="sm" className="gap-1">
                {t('nutrition.view_charts')} <ChevronRight size={16} />
              </Button>
            }
          />
        </div>

        {/* Adherence/Insights */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <TrendingDown className="text-gradient-start" size={20} />
            <h2 className="text-xl font-bold text-text-primary">{t('nutrition.adherence_title')}</h2>
          </div>
          
          <div className="bg-dark-card border border-border rounded-2xl p-6">
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="relative w-32 h-32 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90">
                  <circle
                    cx="64"
                    cy="64"
                    r="58"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="transparent"
                    className="text-white/5"
                  />
                  <circle
                    cx="64"
                    cy="64"
                    r="58"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="transparent"
                    strokeDasharray={364.4}
                    strokeDashoffset={364.4 * (1 - (stats?.stability_score ?? 0) / 100)}
                    className="text-gradient-start"
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-bold">{stats?.stability_score ?? 0}%</span>
                  <span className="text-[10px] text-text-muted font-bold uppercase">{t('nutrition.consistency')}</span>
                </div>
              </div>
              
              <div>
                <h3 className="font-bold">{t('nutrition.stability_score')}</h3>
                <p className="text-sm text-text-secondary mt-1">
                  {t('nutrition.stability_description')}
                </p>
              </div>
            </div>
            
            <div className="mt-8 pt-6 border-t border-border grid grid-cols-7 gap-1">
              {stats?.weekly_adherence.map((adhered, i) => {
                const weeklyDays = t('nutrition.weekly_days', { returnObjects: true }) as string[];
                return (
                  <div key={i} className="flex flex-col items-center gap-1">
                    <div className={cn(
                      "w-full aspect-square rounded-md",
                      adhered ? "bg-gradient-start shadow-orange-sm" : "bg-dark-bg border border-border"
                    )} />
                    <span className="text-[10px] text-text-muted font-medium">
                      {weeklyDays[i]}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
