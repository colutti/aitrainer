import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import type { TrendPoint } from '../../../shared/types/dashboard';

interface WidgetCompositionChartProps {
  title: string;
  data: TrendPoint[];
  color: string;
  gradientId: string;
  unit?: string;
  valueFormatter?: (value: number) => string;
}

export function WidgetCompositionChart({
  title,
  data,
  color,
  gradientId,
  unit = '',
  valueFormatter = (v) => v.toFixed(1)
}: WidgetCompositionChartProps) {
  if (data.length === 0) return null;

  const values = data.map(d => d.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const padding = (maxValue - minValue) * 0.2;

  return (
    <div className="bg-dark-card border border-border rounded-2xl p-6 relative overflow-hidden group">
      <div className="relative z-10 flex flex-col h-full justify-between">
        <div className="mb-4">
          <h3 className="text-sm font-bold text-text-secondary uppercase tracking-wider mb-1">
            {title}
          </h3>
          {data.length > 0 && (
            <p className="text-2xl font-bold text-text-primary">
              {valueFormatter(data[data.length - 1]!.value)}
              {unit && <span className="text-base text-text-muted ml-1">{unit}</span>}
            </p>
          )}
        </div>

        <div className="flex-1 min-h-[120px] -mx-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" hide />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  borderColor: '#334155',
                  borderRadius: '8px',
                  color: '#f8fafc'
                }}
                formatter={(value: number) => [
                  `${valueFormatter(value)} ${unit}`,
                  title
                ]}
                labelFormatter={(label: string | number) => {
                  const date = new Date(label);
                  if (isNaN(date.getTime())) return label.toString();
                  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
                }}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke={color}
                strokeWidth={2}
                fillOpacity={1}
                fill={`url(#${gradientId})`}
              />
              <YAxis
                hide
                domain={[minValue - padding, maxValue + padding]}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      {/* Background glow */}
      <div className="absolute right-0 top-0 w-32 h-32 opacity-0 group-hover:opacity-100 blur-3xl transition-opacity" style={{ backgroundColor: `${color}20` }} />
    </div>
  );
}
