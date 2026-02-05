import { create } from 'zustand';

export type ConfirmationType = 'primary' | 'danger';

export interface ConfirmationOptions {
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: ConfirmationType;
}

interface ConfirmationState {
  isOpen: boolean;
  options: ConfirmationOptions;
  resolve: ((value: boolean) => void) | null;
}

interface ConfirmationActions {
  confirm: (options: string | ConfirmationOptions) => Promise<boolean>;
  accept: () => void;
  cancel: () => void;
}

export type ConfirmationStore = ConfirmationState & ConfirmationActions;

/**
 * Confirmation dialog store using Zustand
 *
 * Provides a promise-based confirmation dialog for user actions.
 * Use this for destructive actions like delete, logout, etc.
 */
export const useConfirmationStore = create<ConfirmationStore>((set, get) => ({
  isOpen: false,
  options: { message: '' },
  resolve: null,

  /**
   * Show confirmation dialog and return a promise
   * Promise resolves to true if user accepts, false if user cancels
   *
   * @param options - Confirmation message string or options object
   * @returns Promise that resolves to boolean (true = accept, false = cancel)
   */
  confirm: (options: string | ConfirmationOptions) => {
    const confirmationOptions = typeof options === 'string' 
      ? { message: options } 
      : options;

    return new Promise<boolean>((resolve) => {
      set({
        isOpen: true,
        options: confirmationOptions,
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
      options: { message: '' },
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
      options: { message: '' },
      resolve: null,
    });
  },
}));

/**
 * Hook to use the confirmation store
 */
export const useConfirmation = () => {
  const confirm = useConfirmationStore((state) => state.confirm);
  return { confirm };
};

