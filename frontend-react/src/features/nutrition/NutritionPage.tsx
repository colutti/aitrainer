import { 
  Beef, 
  ChevronRight,
  Droplets,
  Flame, 
  History,
  Plus, 
  TrendingDown,
  Upload, 
  Utensils, 
  Wheat
} from 'lucide-react';
import { useEffect } from 'react';

import { Button } from '../../shared/components/ui/Button';
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
    deleteLog 
  } = useNutritionStore();
  
  const { confirm } = useConfirmation();
  const notify = useNotificationStore();

  useEffect(() => {
    void fetchLogs();
    void fetchStats();
  }, [fetchLogs, fetchStats]);

  const handleDelete = async (id: string) => {
    const isConfirmed = await confirm({
      title: 'Excluir Registro',
      message: 'Tem certeza que deseja excluir este registro nutricional? Os dados de hoje serão atualizados.',
      confirmText: 'Excluir',
      type: 'danger',
    });

    if (isConfirmed) {
      try {
        await deleteLog(id);
        notify.success('Registro excluído com sucesso!');
      } catch {
        notify.error('Erro ao excluir registro.');
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
            Nutrição
          </h1>
          <p className="text-text-secondary mt-1">
            Abasteça seu corpo para o máximo desempenho.
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" size="lg" className="gap-2">
            <Upload size={20} />
            Importar
          </Button>
          <Button variant="primary" size="lg" className="shadow-orange gap-2">
            <Plus size={20} />
            Registrar Refeição
          </Button>
        </div>
      </div>

      {/* Daily Progress */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
          <Flame className="text-orange-500" size={20} />
          Progresso de Hoje
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MacroCard
            label="Calorias"
            value={today?.calories ?? 0}
            unit="kcal"
            percent={((today?.calories ?? 0) / targets) * 100}
            color="primary"
            icon={<Flame size={20} />}
          />
          <MacroCard
            label="Proteínas"
            value={today?.protein_grams ?? 0}
            unit="g"
            percent={((today?.protein_grams ?? 0) / macroTargets.protein) * 100}
            color="red"
            icon={<Beef size={20} />}
          />
          <MacroCard
            label="Carboidratos"
            value={today?.carbs_grams ?? 0}
            unit="g"
            percent={((today?.carbs_grams ?? 0) / macroTargets.carbs) * 100}
            color="blue"
            icon={<Wheat size={20} />}
          />
          <MacroCard
            label="Gorduras"
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
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History className="text-gradient-start" size={20} />
              <h2 className="text-xl font-bold text-text-primary">Histórico</h2>
            </div>
            <Button variant="ghost" size="sm" className="gap-1">
              Ver Gráficos <ChevronRight size={16} />
            </Button>
          </div>

          <div className="space-y-3">
            {isLoading && logs.length === 0 ? (
              [1, 2, 3].map((i) => (
                <div key={i} className="h-20 bg-dark-card rounded-2xl animate-pulse" />
              ))
            ) : logs.length > 0 ? (
              logs.map((log) => (
                <NutritionLogCard 
                  key={log.id} 
                  log={log} 
                  onDelete={(id) => {
                    void handleDelete(id);
                  }}
                />
              ))
            ) : (
              <div className="p-12 text-center bg-dark-card rounded-2xl border border-border border-dashed">
                <p className="text-text-muted">Nenhum registro encontrado no histórico.</p>
              </div>
            )}
          </div>
        </div>

        {/* Adherence/Insights */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <TrendingDown className="text-gradient-start" size={20} />
            <h2 className="text-xl font-bold text-text-primary">Aderência</h2>
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
                  <span className="text-[10px] text-text-muted font-bold uppercase">Consistência</span>
                </div>
              </div>
              
              <div>
                <h3 className="font-bold">Score de Estabilidade</h3>
                <p className="text-sm text-text-secondary mt-1">
                  Baseado na sua variação calórica dos últimos 14 dias. Manter estabilidade é chave para prever resultados.
                </p>
              </div>
            </div>
            
            <div className="mt-8 pt-6 border-t border-border grid grid-cols-7 gap-1">
              {stats?.weekly_adherence.map((adhered, i) => (
                <div key={i} className="flex flex-col items-center gap-1">
                  <div className={cn(
                    "w-full aspect-square rounded-md",
                    adhered ? "bg-gradient-start shadow-orange-sm" : "bg-dark-bg border border-border"
                  )} />
                  <span className="text-[10px] text-text-muted font-medium">
                    {['D', 'S', 'T', 'Q', 'Q', 'S', 'S'][i]}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
