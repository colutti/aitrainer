import { useTranslation } from 'react-i18next';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

import type { StrengthRadarData } from '../../../shared/types/dashboard';

interface WidgetStrengthRadarProps {
  data: StrengthRadarData;
  className?: string; // Allow external layout control
}

export function WidgetStrengthRadar({ data, className }: WidgetStrengthRadarProps) {
  const { t } = useTranslation();
  // Transform object to array for Recharts
  // Order: Push (Top), Pull (Right), Legs (Bottom), Core (Left)
  const chartData = [
    { subject: t('dashboard.radar_push'), A: data.push, fullMark: 1 },
    { subject: t('dashboard.radar_pull'), A: data.pull, fullMark: 1 },
    { subject: t('dashboard.radar_legs'), A: data.legs, fullMark: 1 },
    { subject: t('dashboard.radar_core'), A: data.core ?? 0, fullMark: 1 },
  ];

  return (
    <div className={className}>
      <div className="h-full w-full min-h-[300px] relative">
         {/* Custom Grid/Background could go here */}
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
        
        {/* Overlay Title */}
        <div className="absolute top-4 left-4">
            <h3 className="text-text-primary font-bold text-sm uppercase tracking-wider">{t('dashboard.strength_radar_title')}</h3>
            <p className="text-text-secondary text-xs">{t('dashboard.strength_radar_subtitle')}</p>
        </div>
      </div>
    </div>
  );
}
