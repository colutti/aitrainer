import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ConfirmationModal } from './ConfirmationModal';

describe('ConfirmationModal', () => {
  const defaultOptions = {
    message: 'Are you sure?',
    type: 'primary' as const
  };

  describe('Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(
        <ConfirmationModal
          isOpen={false}
          options={defaultOptions}
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
          options={defaultOptions}
          onAccept={vi.fn()}
          onCancel={vi.fn()}
        />
      );

      expect(screen.getByTestId('confirmation-modal')).toBeInTheDocument();
      expect(screen.getByText('Are you sure?')).toBeInTheDocument();
    });

    it('should render with custom message and title', () => {
      render(
        <ConfirmationModal
          isOpen={true}
          options={{
            title: 'Custom Title',
            message: 'Delete this item permanently?',
            type: 'danger'
          }}
          onAccept={vi.fn()}
          onCancel={vi.fn()}
        />
      );

      expect(screen.getByText('Custom Title')).toBeInTheDocument();
      expect(screen.getByText('Delete this item permanently?')).toBeInTheDocument();
    });
  });

  describe('Buttons', () => {
    it('should render cancel and confirm buttons', () => {
      render(
        <ConfirmationModal
          isOpen={true}
          options={defaultOptions}
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
          options={defaultOptions}
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
          options={defaultOptions}
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
          options={defaultOptions}
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
          options={defaultOptions}
          onAccept={vi.fn()}
          onCancel={onCancel}
        />
      );

      screen.getByTestId('modal-backdrop').click();

      expect(onCancel).toHaveBeenCalledTimes(1);
    });
  });
});
