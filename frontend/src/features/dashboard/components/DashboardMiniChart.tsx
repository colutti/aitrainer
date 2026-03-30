import { Area, AreaChart, ResponsiveContainer, YAxis } from 'recharts';

interface ChartPoint {
  date: string;
  [key: string]: string | number | undefined;
}

interface DashboardMiniChartProps {
  data: ChartPoint[] | null;
  dataKey: string;
  color: string;
  id: string;
}

/**
 * Reusable mini chart component for Dashboard Bento cards.
 * Standardizes gradients and chart configurations.
 */
export function DashboardMiniChart({ data, dataKey, color, id }: DashboardMiniChartProps) {
  if (!data || data.length === 0) return null;

  return (
    <div className="mt-4 h-24 md:h-32 md:absolute md:inset-x-0 md:bottom-0 md:z-0 md:opacity-40 md:group-hover:opacity-100 transition-opacity">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id={`grad-${id}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
              <stop offset="95%" stopColor={color} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <YAxis hide domain={['dataMin - 1', 'dataMax + 1']} />
          <Area 
            type="monotone" 
            dataKey={dataKey} 
            stroke={color} 
            strokeWidth={3} 
            fillOpacity={1} 
            fill={`url(#grad-${id})`} 
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
