import type { HTMLAttributes } from 'react';

import { PREMIUM_UI } from '../../../styles/ui-variants';
import { cn } from '../../../utils/cn';

export interface PremiumCardProps extends HTMLAttributes<HTMLDivElement> {
  withHover?: boolean;
  withPadding?: boolean;
}

export function PremiumCard({ 
  className, 
  children, 
  withHover = true, 
  withPadding = false,
  ...props 
}: PremiumCardProps) {
  return (
    <div
      className={cn(
        PREMIUM_UI.card.base,
        withHover && PREMIUM_UI.card.hover,
        withPadding && PREMIUM_UI.card.padding,
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
