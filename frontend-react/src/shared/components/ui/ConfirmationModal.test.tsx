import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ConfirmationModal } from './ConfirmationModal';

describe('ConfirmationModal', () => {
  describe('Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(
        <ConfirmationModal
          isOpen={false}
          message="Are you sure?"
          onAccept={vi.fn()}
          onCancel={vi.fn()}
        />
      );

      expect(screen.queryByTestId('confirmation-modal')).not.toBeInTheDocument();
    });

    it('should render when isOpen is true', () => {
      render(
        <ConfirmationModal
          isOpen={true}
          message="Are you sure?"
          onAccept={vi.fn()}
          onCancel={vi.fn()}
        />
      );

      expect(screen.getByTestId('confirmation-modal')).toBeInTheDocument();
      expect(screen.getByText('Are you sure?')).toBeInTheDocument();
    });

    it('should render with custom message', () => {
      render(
        <ConfirmationModal
          isOpen={true}
          message="Delete this item permanently?"
          onAccept={vi.fn()}
          onCancel={vi.fn()}
        />
      );

      expect(screen.getByText('Delete this item permanently?')).toBeInTheDocument();
    });
  });

  describe('Buttons', () => {
    it('should render cancel and confirm buttons', () => {
      render(
        <ConfirmationModal
          isOpen={true}
          message="Confirm action?"
          onAccept={vi.fn()}
          onCancel={vi.fn()}
        />
      );

      expect(screen.getByTestId('confirm-cancel')).toBeInTheDocument();
      expect(screen.getByTestId('confirm-accept')).toBeInTheDocument();
    });

    it('should call onCancel when cancel button is clicked', () => {
      const onCancel = vi.fn();

      render(
        <ConfirmationModal
          isOpen={true}
          message="Test"
          onAccept={vi.fn()}
          onCancel={onCancel}
        />
      );

      screen.getByTestId('confirm-cancel').click();

      expect(onCancel).toHaveBeenCalledTimes(1);
    });

    it('should call onAccept when confirm button is clicked', () => {
      const onAccept = vi.fn();

      render(
        <ConfirmationModal
          isOpen={true}
          message="Test"
          onAccept={onAccept}
          onCancel={vi.fn()}
        />
      );

      screen.getByTestId('confirm-accept').click();

      expect(onAccept).toHaveBeenCalledTimes(1);
    });
  });

  describe('Backdrop', () => {
    it('should render backdrop when modal is open', () => {
      render(
        <ConfirmationModal
          isOpen={true}
          message="Test"
          onAccept={vi.fn()}
          onCancel={vi.fn()}
        />
      );

      expect(screen.getByTestId('modal-backdrop')).toBeInTheDocument();
    });

    it('should call onCancel when backdrop is clicked', () => {
      const onCancel = vi.fn();

      render(
        <ConfirmationModal
          isOpen={true}
          message="Test"
          onAccept={vi.fn()}
          onCancel={onCancel}
        />
      );

      screen.getByTestId('modal-backdrop').click();

      expect(onCancel).toHaveBeenCalledTimes(1);
    });
  });
});
