import { useConfirmationStore } from '../../hooks/useConfirmation';

import { ConfirmationModal } from './ConfirmationModal';

/**
 * Confirmation provider component
 *
 * Renders the confirmation modal and connects it to the useConfirmation store.
 * Should be placed at the root of your application.
 *
 * @example
 * ```tsx
 * function App() {
 *   return (
 *     <>
 *       <YourAppContent />
 *       <ConfirmationProvider />
 *     </>
 *   );
 * }
 * ```
 */
export function ConfirmationProvider() {
  const { isOpen, message, accept, cancel } = useConfirmationStore();

  return (
    <ConfirmationModal
      isOpen={isOpen}
      message={message}
      onAccept={accept}
      onCancel={cancel}
    />
  );
}
