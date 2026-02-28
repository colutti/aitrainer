import { useTranslation } from 'react-i18next';
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import type { WeightHistoryPoint } from '../../../shared/types/dashboard';


interface WidgetWeightChartProps {
  data: WeightHistoryPoint[];
}

export function WidgetWeightChart({ data }: WidgetWeightChartProps) {
  const { t, i18n } = useTranslation();
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
          <XAxis dataKey="date" hide />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
            // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
            formatter={((value: number) => [`${value.toFixed(2)} kg`, t('dashboard.chart.weight')]) as any} // eslint-disable-line @typescript-eslint/no-explicit-any
            labelFormatter={(label: string | number) => {
              const date = new Date(label);
              if (isNaN(date.getTime())) return label.toString();
              return date.toLocaleDateString(i18n.language, { day: '2-digit', month: '2-digit' });
            }}
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
