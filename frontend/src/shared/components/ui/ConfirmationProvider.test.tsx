import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useConfirmationStore } from '../../hooks/useConfirmation';

import { ConfirmationProvider } from './ConfirmationProvider';

// Mock the hook
vi.mock('../../hooks/useConfirmation', () => ({
  useConfirmationStore: vi.fn(),
}));

describe('ConfirmationProvider', () => {
  const mockAccept = vi.fn();
  const mockCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render nothing when not open', () => {
    (useConfirmationStore as any).mockReturnValue({
      isOpen: false,
      options: {},
      accept: mockAccept,
      cancel: mockCancel,
    });

    render(<ConfirmationProvider />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('should render confirmation modal when open', () => {
    (useConfirmationStore as any).mockReturnValue({
      isOpen: true,
      options: { title: 'Confirm Delete', message: 'Are you sure?' },
      accept: mockAccept,
      cancel: mockCancel,
    });

    render(<ConfirmationProvider />);
    expect(screen.getByText('Confirm Delete')).toBeInTheDocument();
    expect(screen.getByText('Are you sure?')).toBeInTheDocument();
  });

  it('should call accept when confirm button is clicked', () => {
    (useConfirmationStore as any).mockReturnValue({
      isOpen: true,
      options: { confirmText: 'Yes' },
      accept: mockAccept,
      cancel: mockCancel,
    });

    render(<ConfirmationProvider />);
    const confirmBtn = screen.getByRole('button', { name: /Yes/i });
    fireEvent.click(confirmBtn);

    expect(mockAccept).toHaveBeenCalled();
  });

  it('should call cancel when cancel button is clicked', () => {
    (useConfirmationStore as any).mockReturnValue({
      isOpen: true,
      options: { cancelText: 'No' },
      accept: mockAccept,
      cancel: mockCancel,
    });

    render(<ConfirmationProvider />);
    const cancelBtn = screen.getByRole('button', { name: /No/i });
    fireEvent.click(cancelBtn);

    expect(mockCancel).toHaveBeenCalled();
  });
});
