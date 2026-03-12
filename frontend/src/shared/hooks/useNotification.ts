import { create } from 'zustand';

export type NotificationType = 'success' | 'error' | 'info';

export interface Notification {
  id: string;
  message: string;
  type: NotificationType;
}

interface NotificationState {
  notifications: Notification[];
}

interface NotificationActions {
  show: (message: string, type: NotificationType, duration?: number) => void;
  success: (message: string, duration?: number) => void;
  error: (message: string, duration?: number) => void;
  info: (message: string, duration?: number) => void;
  remove: (id: string) => void;
  clear: () => void;
}

type NotificationStore = NotificationState & NotificationActions;

/**
 * Notification store using Zustand
 *
 * Manages toast notifications with auto-dismiss functionality.
 * Notifications are displayed as toasts and automatically removed after a duration.
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { success, error } = useNotificationStore();
 *
 *   const handleSave = async () => {
 *     try {
 *       await saveData();
 *       success('Data saved successfully!');
 *     } catch (err) {
 *       error('Failed to save data');
 *     }
 *   };
 *
 *   return <button onClick={handleSave}>Save</button>;
 * }
 * ```
 */
export const useNotificationStore = create<NotificationStore>((set, get) => ({
  notifications: [],

  /**
   * Show a notification toast
   *
   * @param message - Notification message
   * @param type - Notification type (success, error, info)
   * @param duration - Auto-dismiss duration in milliseconds (default: 5000)
   */
  show: (message: string, type: NotificationType, duration = 5000) => {
    const id = `${Date.now().toString()}-${Math.random().toString()}`;

    const notification: Notification = {
      id,
      message,
      type,
    };

    set((state) => ({
      notifications: [...state.notifications, notification],
    }));

    // Auto-remove after duration
    setTimeout(() => {
      get().remove(id);
    }, duration);
  },

  /**
   * Show a success notification
   */
  success: (message: string, duration?: number) => {
    get().show(message, 'success', duration);
  },

  /**
   * Show an error notification
   */
  error: (message: string, duration?: number) => {
    get().show(message, 'error', duration);
  },

  /**
   * Show an info notification
   */
  info: (message: string, duration?: number) => {
    get().show(message, 'info', duration);
  },

  /**
   * Remove a notification by ID
   */
  remove: (id: string) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },

  /**
   * Clear all notifications
   */
  clear: () => {
    set({ notifications: [] });
  },
}));
