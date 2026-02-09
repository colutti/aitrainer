import { Area, AreaChart, ResponsiveContainer, Tooltip, YAxis } from 'recharts';

import type { WeightHistoryPoint } from '../../../shared/types/dashboard';


interface WidgetWeightChartProps {
  data: WeightHistoryPoint[];
}

export function WidgetWeightChart({ data }: WidgetWeightChartProps) {
  if (data.length === 0) return null;

  // Calculate domain for better visualization
  const weights = data.map(d => d.weight);
  const minWeight = Math.min(...weights);
  const maxWeight = Math.max(...weights);
  const padding = (maxWeight - minWeight) * 0.2; // 20% padding

  return (
    <div className="h-full w-full min-h-[120px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorWeight" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <Tooltip 
            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
            formatter={(value: number) => [`${value.toString()} kg`, 'Peso']}
            labelFormatter={(label: string | number) => new Date(label).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
          />
          <Area 
            type="monotone" 
            dataKey="weight" 
            stroke="#10b981" 
            strokeWidth={2}
            fillOpacity={1} 
            fill="url(#colorWeight)" 
          />
           <YAxis 
            hide 
            domain={[minWeight - padding, maxWeight + padding]} 
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
