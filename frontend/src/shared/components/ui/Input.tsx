import { forwardRef } from 'react';

import { cn } from '../../utils/cn';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  leftIcon?: React.ReactNode;
}

/**
 * Premium Input component with labels and error messages
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, leftIcon, type, ...props }, ref) => {
    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label 
            htmlFor={props.id}
            className="text-sm font-medium text-text-secondary px-1"
          >
            {label}
          </label>
        )}
        <div className="relative group">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary transition-colors group-focus-within:text-text-primary">
              {leftIcon}
            </div>
          )}
          <input
            type={type}
            className={cn(
              'form-field flex h-11 w-full px-3 py-2 text-sm',
              leftIcon && 'pl-10',
              error && 'border-red-500 focus:ring-red-500/20 focus:border-red-500',
              className
            )}
            ref={ref}
            {...props}
          />
        </div>
        {error && <p className="text-xs font-medium text-red-500 px-1">{error}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
