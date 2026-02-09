import { CheckCircle, Info, X, XCircle } from 'lucide-react';

import type { NotificationType } from '../../hooks/useNotification';

interface ToastProps {
  id: string;
  message: string;
  type: NotificationType;
  onClose: () => void;
}

const typeStyles: Record<NotificationType, string> = {
  success: 'bg-green-500/10 border-green-500/20 text-green-400',
  error: 'bg-red-500/10 border-red-500/20 text-red-400',
  info: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
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
        shadow-lg backdrop-blur-sm
      `}
    >
      <div className="flex-shrink-0">{icons[type]}</div>

      <p className="flex-1 text-sm font-medium text-text-primary">{message}</p>

      <button
        data-testid="toast-close"
        onClick={onClose}
        className="flex-shrink-0 p-1 rounded-md hover:bg-white/10 transition-colors"
        aria-label="Close notification"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
