import { cn } from '../../../shared/utils/cn';

interface MacroCardProps {
  label: string;
  value: string | number;
  unit: string;
  percent: number;
  color: 'primary' | 'blue' | 'green' | 'red';
  icon: React.ReactNode;
}

/**
 * MacroCard component
 * 
 * Displays a single macronutrient with a progress bar and premium styling.
 */
export function MacroCard({ label, value, unit, percent, color, icon }: MacroCardProps) {
  const colors = {
    primary: 'from-gradient-start to-gradient-end bg-gradient-start',
    blue: 'from-blue-500 to-blue-600 bg-blue-500',
    green: 'from-emerald-500 to-emerald-600 bg-emerald-500',
    red: 'from-red-500 to-red-600 bg-red-500',
  };

  const bgColors = {
    primary: 'bg-gradient-start/10 text-gradient-start',
    blue: 'bg-blue-500/10 text-blue-500',
    green: 'bg-emerald-500/10 text-emerald-500',
    red: 'bg-red-500/10 text-red-500',
  };

  return (
    <div className="bg-dark-card border border-border rounded-2xl p-5 hover:border-border/80 transition-all">
      <div className="flex items-center justify-between mb-4">
        <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center", bgColors[color])}>
          {icon}
        </div>
        <div className="text-right">
          <p className="text-xs text-text-muted font-medium uppercase tracking-wider">{label}</p>
          <p className="text-lg font-bold text-text-primary leading-none mt-1">
            {value} <span className="text-xs font-normal text-text-secondary">{unit}</span>
          </p>
        </div>
      </div>
      
      <div className="space-y-2">
        <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-text-muted">
          <span>Progresso</span>
          <span>{Math.min(percent, 100).toString()}%</span>
        </div>
        <div className="h-2 w-full bg-dark-bg rounded-full overflow-hidden border border-border/30">
          <div 
            className={cn("h-full rounded-full bg-gradient-to-r transition-all duration-1000", colors[color])}
            style={{ width: `${Math.min(percent, 100).toString()}%` }}
          />
        </div>
      </div>
    </div>
  );
}
