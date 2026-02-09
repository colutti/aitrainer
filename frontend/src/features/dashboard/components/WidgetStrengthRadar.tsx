import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

import type { StrengthRadarData } from '../../../shared/types/dashboard';

interface WidgetStrengthRadarProps {
  data: StrengthRadarData;
  className?: string; // Allow external layout control
}

export function WidgetStrengthRadar({ data, className }: WidgetStrengthRadarProps) {
  // Transform object to array for Recharts
  // Order: Push (Top), Pull (Right), Legs (Bottom), Core (Left)
  const chartData = [
    { subject: 'Push', A: data.push, fullMark: 1 },
    { subject: 'Pull', A: data.pull, fullMark: 1 },
    { subject: 'Legs', A: data.legs, fullMark: 1 },
    { subject: 'Core', A: data.core ?? 0, fullMark: 1 },
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
              name="Strength"
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
            <h3 className="text-text-primary font-bold text-sm uppercase tracking-wider">Balanço de Força</h3>
            <p className="text-text-secondary text-xs">Análise relativa (0-1)</p>
        </div>
      </div>
    </div>
  );
}
