import { cn } from '../../utils/cn';

interface UserAvatarProps {
  photo?: string | null;
  name?: string | null;
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  className?: string;
}

/**
 * UserAvatar component
 *
 * Displays user profile photo or initial letter in a circle.
 * Falls back to initial if no photo is provided.
 */
export function UserAvatar({ photo, name, size = 'md', className }: UserAvatarProps) {
  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-20 h-20 text-2xl',
    xl: 'w-32 h-32 text-4xl',
    '2xl': 'w-48 h-48 text-6xl',
  };

  if (photo) {
    return (
      <img
        src={photo}
        alt="User avatar"
        className={cn('rounded-full object-cover', sizeClasses[size], className)}
      />
    );
  }

  const initial = name?.[0]?.toUpperCase() ?? '?';

  return (
    <div
      className={cn(
        'rounded-full bg-gradient-to-br from-gradient-start to-gradient-start/70 flex items-center justify-center text-white font-bold flex-shrink-0',
        sizeClasses[size],
        className
      )}
    >
      {initial}
    </div>
  );
}
