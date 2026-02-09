import { Flame } from 'lucide-react';

interface WidgetStreakProps {
  currentWeeks?: number;
  currentDays?: number;
}

export function WidgetStreak({ currentWeeks = 0, currentDays = 0 }: WidgetStreakProps) {
  return (
    <div className="flex items-center gap-2.5 bg-orange-500/5 border border-orange-500/20 px-4 py-2 rounded-xl h-[46px] transition-all hover:bg-orange-500/10 cursor-default">
      <div className="text-orange-400">
        <Flame size={18} fill="currentColor" className="animate-pulse" />
      </div>
      <div className="flex flex-col justify-center">
        <p className="text-[9px] text-orange-400/70 font-bold uppercase tracking-widest leading-none mb-0.5">Sequência</p>
        <div className="flex items-baseline gap-1 leading-none">
          <span className="text-sm font-black text-white">{currentWeeks}</span>
          <span className="text-[9px] text-text-muted font-bold uppercase">w</span>
          {currentDays > 0 && (
            <>
              <span className="text-[9px] text-text-muted mx-0.5">•</span>
              <span className="text-sm font-bold text-white">{currentDays}</span>
              <span className="text-[9px] text-text-muted font-bold uppercase">d</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
