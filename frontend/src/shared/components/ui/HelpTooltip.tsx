import { HelpCircle } from 'lucide-react';
import { useState } from 'react';

import { cn } from '../../utils/cn';

import { Button } from './Button';

interface HelpTooltipProps {
  content: string;
  className?: string;
}

export function HelpTooltip({ content, className }: HelpTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className={cn("relative inline-flex items-center", className)}>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-6 w-6 text-text-muted/50 hover:text-text-primary hover:bg-transparent"
        onMouseEnter={() => { setIsVisible(true); }}
        onMouseLeave={() => { setIsVisible(false); }}
        onTouchStart={() => { setIsVisible(!isVisible); }}
      >
        <HelpCircle size={16} />
      </Button>

      {isVisible && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 w-64 p-4 z-50 rounded-2xl bg-dark-card border border-border shadow-2xl backdrop-blur-xl animate-in fade-in zoom-in-95 duration-200">
          <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-dark-card border-b border-r border-border rotate-45" />
          <p className="text-xs text-text-secondary leading-relaxed font-medium">
            {content}
          </p>
        </div>
      )}
    </div>
  );
}
