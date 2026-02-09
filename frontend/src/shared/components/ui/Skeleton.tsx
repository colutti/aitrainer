import { cn } from '../../utils/cn';

interface SkeletonProps {
  variant?: 'card' | 'line' | 'circle';
  className?: string;
}

/**
 * Loading skeleton component for placeholder content
 */
export function Skeleton({ variant = 'line', className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse bg-zinc-800/50',
        variant === 'card' && 'h-32 rounded-xl',
        variant === 'line' && 'h-4 rounded',
        variant === 'circle' && 'h-12 w-12 rounded-full',
        className
      )}
    />
  );
}
