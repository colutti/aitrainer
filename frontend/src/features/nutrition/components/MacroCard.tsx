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
    primary: 'bg-primary',
    blue: 'bg-blue-500',
    green: 'bg-emerald-500',
    red: 'bg-red-500',
  };

  const bgColors = {
    primary: 'bg-primary/10 text-primary',
    blue: 'bg-blue-500/10 text-blue-500',
    green: 'bg-emerald-500/10 text-emerald-500',
    red: 'bg-red-500/10 text-red-500',
  };

  return (
    <div className="bg-dark-card border border-border rounded-xl p-5 hover:border-border/80 transition-colors duration-150">
      <div className="flex items-center justify-between mb-4">
        <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", bgColors[color])}>
          {icon}
        </div>
        <div className="text-right">
          <p className="text-xs text-text-muted font-black uppercase tracking-wider">{label}</p>
          <p className="text-lg font-black text-text-primary leading-none mt-1 tracking-tight">
            {value} <span className="text-xs font-medium text-text-secondary">{unit}</span>
          </p>
        </div>
      </div>
      
      <div className="space-y-2">
        <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-text-muted">
          <span>Progresso</span>
          <span>{Math.min(percent, 100).toString()}%</span>
        </div>
        <div className="h-1.5 w-full bg-dark-bg rounded-full overflow-hidden border border-border/30">
          <div 
            className={cn("h-full transition-all duration-700", colors[color])}
            style={{ width: `${Math.min(percent, 100).toString()}%` }}
          />
        </div>
      </div>
    </div>
  );
}
