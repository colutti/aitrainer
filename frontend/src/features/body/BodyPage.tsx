import { Scale, Flame } from 'lucide-react';
import { useLocation } from 'react-router-dom';

import { NutritionTab } from './components/NutritionTab';
import { WeightTab } from './components/WeightTab';




/**
 * BodyPage component
 * 
 * Tracks weight, body composition, nutrition, and metabolic trends.
 * Uses a tab-based navigation for different health metrics.
 */
export function BodyPage() {
  const location = useLocation();
  const isNutrition = location.pathname.includes('nutrition');
  
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-20">
      {/* Header - Dynamic based on route */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
            {isNutrition ? (
              <>
                <Flame className="text-orange-500" size={32} />
                Dieta & Macros
              </>
            ) : (
              <>
                <Scale className="text-blue-400" size={32} />
                Peso & Corpo
              </>
            )}
          </h1>
          <p className="text-text-secondary mt-1 ml-11">
            {isNutrition 
              ? "Acompanhe sua ingestão calórica e macronutrientes diários."
              : "Gerencie seu histórico de peso e composição corporal."
            }
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="min-h-[600px] animate-in fade-in slide-in-from-right-4 duration-500">
        {isNutrition ? <NutritionTab /> : <WeightTab />}
      </div>
    </div>
  );
}
