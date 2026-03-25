import { type ReactNode } from 'react';

import { PREMIUM_UI } from '../../../styles/ui-variants';
import { cn } from '../../../utils/cn';

interface FormFieldProps {
  label: string;
  id?: string;
  icon?: ReactNode;
  error?: string;
  children: ReactNode;
  className?: string;
  optional?: boolean;
}

/**
 * Standardized Form Field for Premium UI.
 * Consolidates Label, Icon, and Error message boilerplate.
 */
export function FormField({ 
  label, 
  id,
  icon, 
  error, 
  children, 
  className,
  optional 
}: FormFieldProps) {
  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex justify-between items-center px-1">
        <label htmlFor={id} className={PREMIUM_UI.text.label}>
          <span className="flex items-center gap-2">
            {icon && <span className="text-zinc-400">{icon}</span>}
            {label}
          </span>
        </label>
        {optional && (
          <span className="text-[9px] font-black uppercase text-zinc-600 tracking-widest">
            Opcional
          </span>
        )}
      </div>
      
      <div className="relative group">
        {children}
      </div>

      {error && (
        <p className="text-[10px] font-bold text-red-400 mt-1.5 animate-in fade-in slide-in-from-top-1 ml-1">
          {error}
        </p>
      )}
    </div>
  );
}
