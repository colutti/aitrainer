import { Trash2, TrendingUp, TrendingDown, Scale } from 'lucide-react';

import { Button } from '../../../shared/components/ui/Button';
import { type WeightLog } from '../../../shared/types/body';
import { cn } from '../../../shared/utils/cn';
import { formatDate } from '../../../shared/utils/format-date';

interface WeightLogCardProps {
  log: WeightLog;
  onDelete?: (date: string) => void;
}

/**
 * WeightLogCard component
 * 
 * Displays a weight entry with trend indicators and body composition details.
 */
export function WeightLogCard({ log, onDelete }: WeightLogCardProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(log.date);
    }
  };

  const hasTrend = log.trend_weight !== undefined;
  const isTrendUp = hasTrend && log.weight_kg > (log.trend_weight ?? 0);

  return (
    <div className="bg-dark-card border border-border rounded-2xl p-4 hover:border-gradient-start/30 transition-all group flex items-center gap-4">
      <div className="w-12 h-12 rounded-xl bg-gradient-start/10 flex items-center justify-center text-gradient-start group-hover:scale-110 transition-transform">
        <Scale size={20} />
      </div>
      
      <div className="flex-1 min-w-0">
        <h3 className="font-bold text-text-primary truncate">{formatDate(log.date)}</h3>
        <div className="flex items-center gap-3 mt-1">
          <span className="text-lg font-bold text-text-primary">
            {log.weight_kg.toFixed(1)} <span className="text-xs font-normal text-text-secondary">kg</span>
          </span>
          
          {hasTrend && (
            <div className={cn(
              "flex items-center gap-0.5 text-[10px] font-bold px-1.5 py-0.5 rounded-md",
              isTrendUp ? "bg-red-500/10 text-red-500" : "bg-emerald-500/10 text-emerald-500"
            )}>
              {isTrendUp ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
              Trend: {log.trend_weight?.toFixed(1)} kg
            </div>
          )}
        </div>
      </div>

      <div className="hidden md:flex gap-6 mr-4 text-center">
        {log.body_fat_pct && (
          <div>
            <p className="text-[10px] text-text-muted font-bold uppercase">Gordura</p>
            <p className="text-sm font-bold text-text-primary">{log.body_fat_pct.toFixed(1)}%</p>
          </div>
        )}
        {log.muscle_mass_pct && (
          <div>
            <p className="text-[10px] text-text-muted font-bold uppercase">Músculo</p>
            <p className="text-sm font-bold text-text-primary">{log.muscle_mass_pct.toFixed(1)}%</p>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <Button 
          variant="danger" 
          size="icon" 
          onClick={handleDelete}
          className="opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <Trash2 size={16} />
        </Button>
      </div>
    </div>
  );
}
