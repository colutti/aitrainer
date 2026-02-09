import { cn } from '../../../shared/utils/cn';

interface WidgetWeeklyFrequencyProps {
  days: boolean[]; // 7 booleans (Mon-Sun)
  className?: string;
}

export function WidgetWeeklyFrequency({ days, className }: WidgetWeeklyFrequencyProps) {
  if (days.length !== 7) return null;

  const dayLabels = ['S', 'T', 'Q', 'Q', 'S', 'S', 'D'];

  return (
    <div className={className}>
       <div className="flex items-center justify-between mb-4">
        <div>
          <h4 className="text-sm font-bold text-text-primary">Frequência Semanal</h4>
          <p className="text-[10px] text-text-muted uppercase font-bold tracking-wider">Distribuição atual</p>
        </div>
      </div>

      <div className="flex justify-between items-center gap-2 px-1">
        {days.map((active, index) => (
          <div key={index} className="flex flex-col items-center gap-2">
            <div 
              className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold transition-all duration-500 border",
                active 
                  ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.2)] scale-110" 
                  : "bg-white/5 text-text-muted border-white/5 opacity-50"
              )}
            >
              {dayLabels[index]}
              {active && (
                <div className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
