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
    primary: 'from-gradient-start/10 to-gradient-end/10 text-gradient-start',
    orange: 'from-orange-500/10 to-orange-600/10 text-orange-500',
    blue: 'from-blue-500/10 to-blue-600/10 text-blue-500',
    green: 'from-emerald-500/10 to-emerald-600/10 text-emerald-500',
    secondary: 'from-zinc-700/10 to-zinc-800/10 text-zinc-400',
    purple: 'from-purple-500/10 to-purple-600/10 text-purple-500',
  };

  return (
    <div className="bg-dark-card border border-border rounded-2xl p-6 hover:border-gradient-start/30 transition-all duration-300 group">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-text-secondary text-sm font-medium mb-1">{title}</p>
          <h3 className="text-2xl font-bold text-text-primary tracking-tight">
            {value}
          </h3>
          {subtitle && (
            <p className="text-xs text-text-muted mt-1">{subtitle}</p>
          )}
        </div>
        
        <div className={cn(
          "w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-br transition-transform duration-300 group-hover:scale-110",
          variants[variant]
        )}>
          {icon}
        </div>
      </div>

      {(trend ?? trendValue ?? false) && (
        <div className="mt-4 pt-4 border-t border-border flex items-center gap-2">
          {trend && (
            <span className={cn(
              "text-xs font-bold px-2 py-0.5 rounded-full capitalize",
              trend === 'down' ? 'bg-red-500/10 text-red-500' : 
              trend === 'up' ? 'bg-emerald-500/10 text-emerald-500' : 
              'bg-blue-500/10 text-blue-500'
            )}>
              {t(`common.trends.${trend}`)}
            </span>
          )}
          {trendValue && (
            <span className="text-xs text-text-secondary">{trendValue}</span>
          )}
        </div>
      )}
    </div>
  );
}
