import { useTranslation } from "react-i18next";

import { cn } from '../../utils/cn';

interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
  variant?: 'primary' | 'orange' | 'blue' | 'green' | 'secondary' | 'purple';
}

/**
 * StatsCard component
 * 
 * Displays a single statistic value with an icon and optional trend information.
 * Uses a premium card style with gradients and subtle shadows.
 */
export function StatsCard({ 
  title, 
  value, 
  subtitle, 
  icon, 
  trend, 
  trendValue,
  variant = 'primary'
}: StatsCardProps) {
  const { t } = useTranslation();
  const variants = {
    primary: 'bg-primary/10 text-primary border-primary/20',
    orange: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
    blue: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    green: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
    secondary: 'bg-zinc-700/10 text-zinc-400 border-zinc-700/20',
    purple: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
  };

  return (
    <div className="bg-dark-card border border-border rounded-xl p-5 hover:border-primary/50 transition-colors duration-150 group">
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-text-secondary text-[13px] font-semibold mb-1">{title}</p>
          <h3 className="text-2xl font-bold text-text-primary tracking-tight">
            {value}
          </h3>
          {subtitle && (
            <p className="text-xs text-text-muted mt-1.5 font-medium">{subtitle}</p>
          )}
        </div>
        
        <div className={cn(
          "w-11 h-11 rounded-lg flex items-center justify-center border transition-colors duration-150",
          variants[variant]
        )}>
          {icon}
        </div>
      </div>

      {(trend ?? trendValue ?? false) && (
        <div className="mt-4 pt-4 border-t border-border flex items-center gap-2">
          {trend && (
            <span className={cn(
              "text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider",
              trend === 'down' ? 'bg-red-500/10 text-red-500 border border-red-500/10' : 
              trend === 'up' ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/10' : 
              'bg-blue-500/10 text-blue-500 border border-blue-500/10'
            )}>
              {t(`common.trends.${trend}`)}
            </span>
          )}
          {trendValue && (
            <span className="text-xs text-text-muted font-bold">{trendValue}</span>
          )}
        </div>
      )}
    </div>
  );
}
