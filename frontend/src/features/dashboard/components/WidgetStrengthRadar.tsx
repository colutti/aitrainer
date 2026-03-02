import { Activity } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

import type { StrengthRadarData } from '../../../shared/types/dashboard';
import { cn } from '../../../shared/utils/cn';

import { NoDataOverlay } from './NoDataOverlay';

interface WidgetStrengthRadarProps {
  data?: StrengthRadarData | null;
  className?: string; // Allow external layout control
}

export function WidgetStrengthRadar({ data, className }: WidgetStrengthRadarProps) {
  const { t } = useTranslation();
  const isEmpty = !data;

  // Use dummy data if empty to show the shape
  const displayData = data ?? { push: 0.5, pull: 0.4, legs: 0.6, core: 0.3 };

  // Transform object to array for Recharts
  // Order: Push (Top), Pull (Right), Legs (Bottom), Core (Left)
  const chartData = [
    { subject: t('dashboard.radar_push'), A: displayData.push, fullMark: 1 },
    { subject: t('dashboard.radar_pull'), A: displayData.pull, fullMark: 1 },
    { subject: t('dashboard.radar_legs'), A: displayData.legs, fullMark: 1 },
    { subject: t('dashboard.radar_core'), A: displayData.core ?? 0, fullMark: 1 },
  ];

   return (
    <div className={cn("relative group transition-all duration-500 h-full flex flex-col min-h-[300px]", className)}>
      <div className="flex items-center gap-3 mb-4">
        <div className="h-8 w-8 rounded-lg bg-violet-500/10 text-violet-500 flex items-center justify-center">
          <Activity size={16} />
        </div>
        <div>
          <h4 className="text-sm font-bold text-text-primary">{t('dashboard.strength_radar_title')}</h4>
          <p className="text-[10px] text-text-muted uppercase font-bold tracking-wider">{t('dashboard.strength_radar_subtitle')}</p>
        </div>
      </div>

      <div className={cn("flex-1 w-full relative transition-all duration-700", isEmpty && "blur-sm grayscale opacity-30 select-none")}>
         <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="70%" data={chartData}>
            <PolarGrid stroke="#334155" />
            <PolarAngleAxis 
                dataKey="subject" 
                tick={{ fill: '#94a3b8', fontSize: 12, fontWeight: 'bold' }} 
            />
            <PolarRadiusAxis angle={30} domain={[0, 1]} tick={false} axisLine={false} />
            <Radar
              name={t('dashboard.radar_strength')}
              dataKey="A"
              stroke="#8b5cf6"
              strokeWidth={2}
              fill="#8b5cf6"
              fillOpacity={0.3}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      
      {isEmpty && <NoDataOverlay message={t('dashboard.insufficient_strength_data')} />}
    </div>
  );
}
