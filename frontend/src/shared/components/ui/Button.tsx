import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '../../utils/cn';

const buttonVariants = cva(
  'inline-flex appearance-none items-center justify-center gap-2 rounded-[var(--radius-md)] border text-sm font-semibold transition-[background-color,border-color,color,transform] duration-200 outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--color-primary)]/20 disabled:pointer-events-none disabled:opacity-50 active:translate-y-px [-webkit-tap-highlight-color:transparent]',
  {
    variants: {
      variant: {
        primary:
          'border-transparent bg-[color:var(--color-primary)] text-[color:var(--color-on-primary)] hover:bg-[color:var(--color-primary-container)]',
        secondary:
          'border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-high)] text-[color:var(--color-on-surface)] hover:bg-[color:var(--color-surface-container-highest)]',
        ghost:
          'border-transparent bg-transparent text-[color:var(--color-on-surface-variant)] hover:bg-[color:var(--color-surface-container)] hover:text-[color:var(--color-on-surface)] active:bg-[color:var(--color-surface-container-high)]',
        danger:
          'border-transparent bg-[color:var(--color-error)] text-[color:var(--color-on-error)] hover:opacity-90',
      },
      size: {
        default: 'h-11 px-6 py-2',
        sm: 'h-9 px-4 rounded-[var(--radius-default)]',
        lg: 'h-12 px-8',
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
