import { Trophy, ArrowUpRight } from 'lucide-react';

import type { PRRecord } from '../../../shared/types/dashboard';

interface WidgetRecentPRsProps {
  prs: PRRecord[];
}

export function WidgetRecentPRs({ prs }: WidgetRecentPRsProps) {
  if (!prs.length) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Trophy className="text-yellow-500" size={20} />
        <h2 className="text-lg font-bold text-text-primary">Recordes Recentes</h2>
      </div>
      
      <div className="grid gap-3">
        {prs.map((pr) => (
          <div 
            key={pr.id} 
            className="flex items-center justify-between p-4 bg-dark-card border border-border rounded-xl hover:border-yellow-500/30 transition-colors group relative overflow-hidden"
          >
            {/* Background glow effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-yellow-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

            <div className="flex items-center gap-4 relative z-10">
              <div className="h-10 w-10 rounded-full bg-yellow-500/10 flex items-center justify-center text-yellow-500 font-bold text-xs ring-1 ring-yellow-500/20 group-hover:ring-yellow-500/40 transition-all">
                PR
              </div>
              <div>
                <h4 className="font-bold text-text-primary group-hover:text-yellow-400 transition-colors">{pr.exercise}</h4>
                <p className="text-xs text-text-secondary">
                  {new Date(pr.date).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })} • {pr.reps} reps
                </p>
              </div>
            </div>

            <div className="text-right relative z-10">
              <div className="flex items-center gap-1 justify-end">
                <span className="text-xl font-black text-white tracking-tight">{pr.weight}<span className="text-sm font-medium text-text-muted ml-0.5">kg</span></span>
              </div>
              {pr.previous_weight && (
                 <div className="flex items-center justify-end gap-1 text-xs text-emerald-400 font-medium">
                    <ArrowUpRight size={12} />
                    <span>+{((pr.weight - pr.previous_weight)).toFixed(1)}kg</span>
                 </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
