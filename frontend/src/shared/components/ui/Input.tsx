import { forwardRef } from 'react';

import { cn } from '../../utils/cn';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  leftIcon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, leftIcon, type, ...props }, ref) => {
    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label
            htmlFor={props.id}
            className="px-0.5 text-[13px] font-medium uppercase tracking-[0.05em] text-[color:var(--color-on-surface-variant)]"
          >
            {label}
          </label>
        )}
        <div className="relative group">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[color:var(--color-on-surface-variant)] transition-colors group-focus-within:text-[color:var(--color-primary)]">
              {leftIcon}
            </div>
          )}
          <input
            type={type}
            className={cn(
              'flex h-11 w-full rounded-[var(--radius-md)] border border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] px-3 py-2 text-sm text-[color:var(--color-on-surface)] placeholder:text-[color:var(--color-on-surface-variant)] transition-[border-color,box-shadow,background-color] duration-200 outline-none focus-visible:border-[color:var(--color-primary)] focus-visible:ring-2 focus-visible:ring-[color:var(--color-primary)]/20 disabled:cursor-not-allowed disabled:opacity-50',
              leftIcon && 'pl-10',
              error &&
                'border-[color:var(--color-error)] focus-visible:border-[color:var(--color-error)] focus-visible:ring-[color:var(--color-error)]/20',
              className
            )}
            ref={ref}
            aria-invalid={Boolean(error)}
            {...props}
          />
        </div>
        {error && <p className="px-0.5 text-xs font-medium text-[color:var(--color-error)]">{error}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
