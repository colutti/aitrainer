import { AlertTriangle } from 'lucide-react';

interface ConfirmationModalProps {
  isOpen: boolean;
  message: string;
  onAccept: () => void;
  onCancel: () => void;
}

/**
 * Confirmation modal component
 *
 * Displays a modal dialog for confirming destructive actions.
 * Used by the useConfirmation store to show confirmation dialogs.
 *
 * @example
 * ```tsx
 * <ConfirmationModal
 *   isOpen={isOpen}
 *   message="Are you sure you want to delete this item?"
 *   onAccept={handleAccept}
 *   onCancel={handleCancel}
 * />
 * ```
 */
export function ConfirmationModal({
  isOpen,
  message,
  onAccept,
  onCancel,
}: ConfirmationModalProps) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        data-testid="modal-backdrop"
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Modal */}
      <div
        data-testid="confirmation-modal"
        className="relative bg-dark-card border border-border rounded-lg p-6 max-w-md w-full shadow-xl animate-in zoom-in-95"
      >
        {/* Icon */}
        <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 rounded-full bg-orange-500/10">
          <AlertTriangle className="h-6 w-6 text-orange-500" />
        </div>

        {/* Message */}
        <p className="text-center text-text-primary mb-6">{message}</p>

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            data-testid="confirm-cancel"
            onClick={onCancel}
            className="flex-1 px-4 py-2 rounded-md bg-dark-bg border border-border text-text-primary hover:bg-dark-bg/80 transition-colors"
          >
            Cancelar
          </button>
          <button
            data-testid="confirm-accept"
            onClick={onAccept}
            className="flex-1 px-4 py-2 rounded-md bg-gradient-to-r from-gradient-start to-gradient-end text-white font-medium hover:opacity-90 transition-opacity"
          >
            Confirmar
          </button>
        </div>
      </div>
    </div>
  );
}
