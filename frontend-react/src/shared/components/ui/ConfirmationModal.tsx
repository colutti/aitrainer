import { AlertTriangle, Info } from 'lucide-react';

import { type ConfirmationOptions } from '../../hooks/useConfirmation';
import { cn } from '../../utils/cn';

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
            isDanger ? "bg-red-500/10 text-red-500" : "bg-gradient-start/10 text-gradient-start"
          )}>
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
          <button
            data-testid="confirm-cancel"
            onClick={onCancel}
            className="flex-1 h-11 px-4 rounded-xl bg-dark-bg border border-border text-text-primary font-medium hover:bg-white/5 transition-all active:scale-95"
          >
            {options.cancelText ?? 'Cancelar'}
          </button>
          <button
            data-testid="confirm-accept"
            onClick={onAccept}
            className={cn(
              "flex-1 h-11 px-4 rounded-xl text-white font-bold transition-all active:scale-95 shadow-lg",
              isDanger 
                ? "bg-red-500 hover:bg-red-600 shadow-red-500/20" 
                : "bg-gradient-to-r from-gradient-start to-gradient-end hover:opacity-90 shadow-orange"
            )}
          >
            {options.confirmText ?? 'Confirmar'}
          </button>
        </div>
      </div>
    </div>
  );
}

