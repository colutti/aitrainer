import { create } from 'zustand';

interface ConfirmationState {
  isOpen: boolean;
  message: string;
  resolve: ((value: boolean) => void) | null;
}

interface ConfirmationActions {
  confirm: (message: string) => Promise<boolean>;
  accept: () => void;
  cancel: () => void;
}

type ConfirmationStore = ConfirmationState & ConfirmationActions;

/**
 * Confirmation dialog store using Zustand
 *
 * Provides a promise-based confirmation dialog for user actions.
 * Use this for destructive actions like delete, logout, etc.
 *
 * @example
 * ```tsx
 * function DeleteButton({ itemId }: { itemId: string }) {
 *   const { confirm } = useConfirmationStore();
 *
 *   const handleDelete = async () => {
 *     const confirmed = await confirm('Are you sure you want to delete this item?');
 *     if (confirmed) {
 *       await deleteItem(itemId);
 *     }
 *   };
 *
 *   return <button onClick={handleDelete}>Delete</button>;
 * }
 * ```
 */
export const useConfirmationStore = create<ConfirmationStore>((set, get) => ({
  isOpen: false,
  message: '',
  resolve: null,

  /**
   * Show confirmation dialog and return a promise
   * Promise resolves to true if user accepts, false if user cancels
   *
   * @param message - Confirmation message to display
   * @returns Promise that resolves to boolean (true = accept, false = cancel)
   */
  confirm: (message: string) => {
    return new Promise<boolean>((resolve) => {
      set({
        isOpen: true,
        message,
        resolve,
      });
    });
  },

  /**
   * Accept the confirmation
   * Closes the dialog and resolves the promise with true
   */
  accept: () => {
    const { resolve } = get();
    if (resolve) {
      resolve(true);
    }
    set({
      isOpen: false,
      message: '',
      resolve: null,
    });
  },

  /**
   * Cancel the confirmation
   * Closes the dialog and resolves the promise with false
   */
  cancel: () => {
    const { resolve } = get();
    if (resolve) {
      resolve(false);
    }
    set({
      isOpen: false,
      message: '',
      resolve: null,
    });
  },
}));
