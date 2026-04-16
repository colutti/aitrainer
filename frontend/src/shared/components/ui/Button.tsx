import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '../../utils/cn';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all appearance-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/30 disabled:opacity-50 disabled:pointer-events-none active:scale-95 [-webkit-tap-highlight-color:transparent]',
  {
    variants: {
      variant: {
        primary: 'bg-[#14b8a6] text-black border border-[#2dd4bf]/30 hover:bg-[#0d9488] shadow-none',
        secondary: 'bg-[color:var(--color-app-surface-raised)] border border-white/10 text-[color:var(--color-text-primary)] hover:bg-[#1a1a1a]',
        ghost: 'text-text-secondary hover:text-text-primary hover:bg-white/5 active:bg-white/10',
        danger: 'bg-red-500/10 border border-red-500/20 text-red-500 hover:bg-red-500/20',
      },
      size: {
        default: 'h-11 px-6 py-2',
        sm: 'h-9 px-4 rounded-md',
        lg: 'h-12 px-8 rounded-xl',
        icon: 'h-10 w-10',
      },
      fullWidth: {
        true: 'w-full',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'default',
    },
  }
);

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean;
}

/**
 * Premium Button component with multiple variants and sizes
 */
export function Button({
  className,
  variant,
  size,
  fullWidth,
  isLoading,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size, fullWidth }), className)}
      disabled={Boolean(isLoading) || Boolean(disabled)}
      {...props}
    >
      {isLoading ? (
        <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      ) : null}
      {children}
    </button>
  );
}
