import { AlertTriangle, Info } from 'lucide-react';

import { type ConfirmationOptions } from '../../hooks/useConfirmation';
import { cn } from '../../utils/cn';

import { Button } from './Button';

interface ConfirmationModalProps {
  isOpen: boolean;
  options: ConfirmationOptions;
  onAccept: () => void;
  onCancel: () => void;
}

/**
 * Confirmation modal component
 *
 * Displays a modal dialog for confirming actions.
 * Supports multiple variants (danger, primary) and custom content.
 */
export function ConfirmationModal({
  isOpen,
  options,
  onAccept,
  onCancel,
}: ConfirmationModalProps) {
  if (!isOpen) {
    return null;
  }

  const isDanger = options.type === 'danger';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
      {/* Backdrop */}
      <div
        data-testid="modal-backdrop"
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Modal */}
      <div
        data-testid="confirmation-modal"
        className="relative bg-dark-card border border-border rounded-2xl p-6 max-w-md w-full shadow-2xl animate-in zoom-in-95 duration-200"
      >
        {/* Icon & Title */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className={cn(
            "w-12 h-12 rounded-full flex items-center justify-center mb-4",
            isDanger ? "bg-red-500/10 text-red-500" : "bg-white/10 text-text-primary"
          )}
            data-testid="confirmation-icon-badge"
          >
            {isDanger ? <AlertTriangle size={24} /> : <Info size={24} />}
          </div>
          <h3 className="text-xl font-bold text-text-primary">
            {options.title ?? 'Confirmar Ação'}
          </h3>
        </div>

        {/* Message */}
        <p className="text-center text-text-secondary mb-8">
          {options.message}
        </p>

        {/* Buttons */}
        <div className="flex gap-3">
          <Button
            data-testid="confirm-cancel"
            onClick={onCancel}
            variant="secondary"
            fullWidth
            className="h-11"
          >
            {options.cancelText ?? 'Cancelar'}
          </Button>
          <Button
            data-testid="confirm-accept"
            onClick={onAccept}
            fullWidth
            className={cn(
              "h-11 font-bold text-white",
              isDanger 
                ? "bg-red-500 hover:bg-red-600 border-red-500 shadow-none" 
                : "bg-[#14b8a6] hover:bg-[#0d9488] text-black border-[#2dd4bf]/30 shadow-none"
            )}
          >
            {options.confirmText ?? 'Confirmar'}
          </Button>
        </div>
      </div>
    </div>
  );
}
