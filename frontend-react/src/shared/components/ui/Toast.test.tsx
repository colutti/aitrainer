import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Toast } from './Toast';

describe('Toast', () => {
  describe('Rendering', () => {
    it('should render success toast with correct styling', () => {
      render(
        <Toast
          id="test-1"
          message="Operation successful"
          type="success"
          onClose={vi.fn()}
        />
      );

      const toast = screen.getByText('Operation successful');
      expect(toast).toBeInTheDocument();
      expect(toast.closest('[data-testid="toast"]')).toHaveClass('bg-green-500/10');
    });

    it('should render error toast with correct styling', () => {
      render(
        <Toast id="test-2" message="Operation failed" type="error" onClose={vi.fn()} />
      );

      const toast = screen.getByText('Operation failed');
      expect(toast).toBeInTheDocument();
      expect(toast.closest('[data-testid="toast"]')).toHaveClass('bg-red-500/10');
    });

    it('should render info toast with correct styling', () => {
      render(
        <Toast
          id="test-3"
          message="Information message"
          type="info"
          onClose={vi.fn()}
        />
      );

      const toast = screen.getByText('Information message');
      expect(toast).toBeInTheDocument();
      expect(toast.closest('[data-testid="toast"]')).toHaveClass('bg-blue-500/10');
    });
  });

  describe('Icons', () => {
    it('should show check icon for success toast', () => {
      render(
        <Toast
          id="test-4"
          message="Success"
          type="success"
          onClose={vi.fn()}
        />
      );

      const icon = screen.getByTestId('toast-icon');
      expect(icon).toBeInTheDocument();
    });

    it('should show X icon for error toast', () => {
      render(<Toast id="test-5" message="Error" type="error" onClose={vi.fn()} />);

      const icon = screen.getByTestId('toast-icon');
      expect(icon).toBeInTheDocument();
    });

    it('should show info icon for info toast', () => {
      render(<Toast id="test-6" message="Info" type="info" onClose={vi.fn()} />);

      const icon = screen.getByTestId('toast-icon');
      expect(icon).toBeInTheDocument();
    });
  });

  describe('Close button', () => {
    it('should render close button', () => {
      render(
        <Toast id="test-7" message="Test" type="info" onClose={vi.fn()} />
      );

      const closeButton = screen.getByTestId('toast-close');
      expect(closeButton).toBeInTheDocument();
    });

    it('should call onClose when close button is clicked', () => {
      const onClose = vi.fn();

      render(<Toast id="test-8" message="Test" type="info" onClose={onClose} />);

      const closeButton = screen.getByTestId('toast-close');
      closeButton.click();

      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });
});
