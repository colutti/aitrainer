import { CheckCircle, Info, X, XCircle } from 'lucide-react';

import type { NotificationType } from '../../hooks/useNotification';

import { Button } from './Button';

interface ToastProps {
  id: string;
  message: string;
  type: NotificationType;
  onClose: () => void;
}

const typeStyles: Record<NotificationType, string> = {
  success: 'bg-[color:var(--color-secondary)]/10 border-[color:var(--color-secondary)]/30 text-[color:var(--color-secondary)]',
  error: 'bg-[color:var(--color-error)]/10 border-[color:var(--color-error)]/30 text-[color:var(--color-error)]',
  info: 'bg-[color:var(--color-primary)]/10 border-[color:var(--color-primary)]/30 text-[color:var(--color-primary)]',
};

const icons: Record<NotificationType, React.ReactNode> = {
  success: <CheckCircle className="h-5 w-5" data-testid="toast-icon" />,
  error: <XCircle className="h-5 w-5" data-testid="toast-icon" />,
  info: <Info className="h-5 w-5" data-testid="toast-icon" />,
};

/**
 * Toast notification component
 *
 * Displays a temporary notification message with an icon and close button.
 * Used by the ToastContainer to render individual notifications.
 *
 * @example
 * ```tsx
 * <Toast
 *   id="notification-1"
 *   message="Profile updated successfully"
 *   type="success"
 *   onClose={() => removeNotification('notification-1')}
 * />
 * ```
 */
export function Toast({ id: _id, message, type, onClose }: ToastProps) {
  return (
    <div
      data-testid="toast"
      className={`
        flex items-center gap-3 p-4 rounded-lg border
        ${typeStyles[type]}
        animate-in slide-in-from-right-full
         backdrop-blur-sm
      `}
    >
      <div className="flex-shrink-0">{icons[type]}</div>

      <p className="flex-1 text-sm font-medium text-[color:var(--color-on-surface)]">{message}</p>

      <Button
        data-testid="toast-close"
        onClick={onClose}
        variant="ghost"
        size="icon"
        className="h-6 w-6 flex-shrink-0 rounded-md hover:bg-[color:var(--color-surface-container-high)]"
        aria-label="Close notification"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}
