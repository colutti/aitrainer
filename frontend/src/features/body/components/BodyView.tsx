import { Scale, Flame } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { PREMIUM_UI } from '../../../shared/styles/ui-variants';
import { cn } from '../../../shared/utils/cn';

import { NutritionTab } from './NutritionTab';
import { WeightTab } from './WeightTab';

export type BodyTab = 'weight' | 'nutrition';

export interface BodyViewProps {
  activeTab: BodyTab;
  onTabChange: (tab: BodyTab) => void;
}

export function BodyView({ activeTab, onTabChange }: BodyViewProps) {
  const { t } = useTranslation();

  const tabs = [
    { id: 'weight', label: t('body.weight_title'), icon: Scale },
    { id: 'nutrition', label: t('body.nutrition_title'), icon: Flame },
  ] as const;

  return (
    <div className={cn(PREMIUM_UI.animation.fadeIn, "space-y-8 pb-20")}>
      
      {/* HEADER SECTION */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <p className={PREMIUM_UI.text.label}>
            {activeTab === 'nutrition' ? t('body.nutrition_subtitle') : t('body.weight_subtitle')}
          </p>
          <h1 className={PREMIUM_UI.text.heading}>
            {activeTab === 'nutrition' ? t('body.nutrition_title') : t('body.weight_title')}
          </h1>
        </div>

        {/* PILL TABS */}
        <div className="flex bg-white/5 backdrop-blur-md rounded-full p-1 border border-white/5 w-fit">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                data-testid={`body-tab-${tab.id}`}
                onClick={() => { onTabChange(tab.id as BodyTab); }}
                className={cn(
                  "flex items-center gap-2 px-4 md:px-6 py-2 rounded-full text-xs md:text-sm font-black transition-all uppercase tracking-widest",
                  isActive 
                    ? "bg-white text-black shadow-lg" 
                    : "text-zinc-500 hover:text-zinc-300"
                )}
              >
                <Icon size={16} />
                <span className={cn(isActive ? "block" : "hidden md:block")}>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* TAB CONTENT */}
      <div className="min-h-[500px]">
        {activeTab === 'weight' && <WeightTab />}
        {activeTab === 'nutrition' && <NutritionTab />}
      </div>

    </div>
  );
}
