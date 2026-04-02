import { HelpCircle } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

import { cn } from '../../utils/cn';

import { Button } from './Button';

type TooltipAlign = 'start' | 'center' | 'end';
type TooltipSide = 'top' | 'bottom';

interface HelpTooltipProps {
  content: string;
  className?: string;
  align?: TooltipAlign;
  side?: TooltipSide;
  ariaLabel?: string;
}

const alignStyles: Record<TooltipAlign, string> = {
  start: 'left-0',
  center: 'left-1/2 -translate-x-1/2',
  end: 'right-0',
};

const sideStyles: Record<TooltipSide, string> = {
  top: 'bottom-full mb-3',
  bottom: 'top-full mt-3',
};

const arrowStyles: Record<TooltipSide, string> = {
  top: '-bottom-1.5 border-b border-r',
  bottom: '-top-1.5 border-t border-l',
};

export function HelpTooltip({
  content,
  className,
  align = 'center',
  side = 'top',
  ariaLabel = 'Ajuda',
}: HelpTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handlePointerDown = (event: MouseEvent | TouchEvent) => {
      if (!containerRef.current) return;
      if (event.target instanceof Node && !containerRef.current.contains(event.target)) {
        setIsVisible(false);
      }
    };

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('touchstart', handlePointerDown);

    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('touchstart', handlePointerDown);
    };
  }, []);

  return (
    <div ref={containerRef} className={cn("relative inline-flex items-center", className)}>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-6 w-6 text-text-muted/50 hover:text-text-primary hover:bg-transparent"
        aria-label={ariaLabel}
        onClick={() => { setIsVisible((prev) => !prev); }}
        onMouseEnter={() => { setIsVisible(true); }}
        onMouseLeave={() => { setIsVisible(false); }}
      >
        <HelpCircle size={16} />
      </Button>

      {isVisible && (
        <div
          className={cn(
            "absolute z-50 w-[min(16rem,calc(100vw-2rem))] p-4 rounded-2xl bg-dark-card border border-border shadow-2xl backdrop-blur-xl animate-in fade-in zoom-in-95 duration-200",
            sideStyles[side],
            alignStyles[align]
          )}
          role="tooltip"
        >
          <div
            className={cn(
              "absolute left-3 w-3 h-3 bg-dark-card border-border rotate-45",
              arrowStyles[side]
            )}
          />
          <p className="text-xs text-text-secondary leading-relaxed font-medium">
            {content}
          </p>
        </div>
      )}
    </div>
  );
}
