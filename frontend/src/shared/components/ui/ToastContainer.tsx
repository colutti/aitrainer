import { useNotificationStore } from '../../hooks/useNotification';

import { Toast } from './Toast';

/**
 * Toast container component
 *
 * Renders all active toast notifications in a fixed position.
 * Automatically subscribes to the notification store and displays toasts.
 *
 * @example
 * ```tsx
 * function App() {
 *   return (
 *     <>
 *       <YourAppContent />
 *       <ToastContainer />
 *     </>
 *   );
 * }
 * ```
 */
export function ToastContainer() {
  const { notifications, remove } = useNotificationStore();

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div
      data-testid="toast-container"
      className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-md"
    >
      {notifications.map((notification) => (
        <Toast
          key={notification.id}
          id={notification.id}
          message={notification.message}
          type={notification.type}
          onClose={() => { remove(notification.id); }}
        />
      ))}
    </div>
  );
}
