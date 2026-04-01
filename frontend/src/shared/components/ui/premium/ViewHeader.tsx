import { type ReactNode } from 'react';

import { PREMIUM_UI } from '../../../styles/ui-variants';
import { cn } from '../../../utils/cn';
import { Button } from '../Button';

interface ViewHeaderProps {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  action?: {
    label: string;
    onClick: () => void;
    icon?: ReactNode;
    disabled?: boolean;
  };
  className?: string;
}

/**
 * Standardized Header for Dashboard views.
 * Consolidates Title, Subtitle, optional Icon and primary Action Button.
 */
export function ViewHeader({ title, subtitle, icon, action, className }: ViewHeaderProps) {
  return (
    <div data-testid="view-header" className={cn("flex flex-col md:flex-row md:items-end justify-between gap-6", className)}>
      <div className="flex items-center gap-4">
        {icon && (
          <div data-testid="view-header-icon" className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-zinc-400 shadow-inner">
            {icon}
          </div>
        )}
        <div>
          <h1 data-testid="view-header-title" className={PREMIUM_UI.text.heading}>{title}</h1>
          {subtitle && <p data-testid="view-header-subtitle" className={PREMIUM_UI.text.label}>{subtitle}</p>}
        </div>
      </div>
      
      {action && (
        <Button
          type="button"
          onClick={action.onClick}
          disabled={action.disabled}
          data-testid="view-header-action"
          className={PREMIUM_UI.button.premium}
        >
          {action.icon}
          {action.label}
        </Button>
      )}
    </div>
  );
}
