import { useTranslation } from 'react-i18next';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

interface WidgetVolumeTrendProps {
  data: number[];
  className?: string;
}

export function WidgetVolumeTrend({ data, className }: WidgetVolumeTrendProps) {
  const { t } = useTranslation();
  if (!data.length) return null;

  // Transform data for Recharts: [val, val, ...] -> [{ name: 'Semana X', volume: val }, ...]
  const chartData = data.map((volume, index) => ({
    name: t('dashboard.week_short', { count: index + 1 }),
    volume: Math.round(volume),
  }));

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h4 className="text-sm font-bold text-text-primary">{t('dashboard.volume_trend_title')}</h4>
          <p className="text-[10px] text-text-muted uppercase font-bold tracking-wider">{t('dashboard.volume_trend_subtitle')}</p>
        </div>
      </div>
      
      <div className="flex-1 w-full mt-2 min-h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.3} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
              cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
              // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
              formatter={((value: number) => [`${value.toFixed(2)} kg`, t('dashboard.volume_label')]) as any} // eslint-disable-line @typescript-eslint/no-explicit-any
            />
            <Bar 
              dataKey="volume" 
              fill="#3b82f6" 
              radius={[4, 4, 0, 0]}
              fillOpacity={0.8}
              barSize={20}
            />
            <XAxis 
              dataKey="name" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#94a3b8', fontSize: 10 }}
              dy={10}
            />
            <YAxis 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748b', fontSize: 10 }}
              tickFormatter={(value: number) => value > 0 ? `${(value / 1000).toFixed(0)}k` : '0'}
              width={40}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
