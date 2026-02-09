import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useNotificationStore } from '../../hooks/useNotification';

import { ToastContainer } from './ToastContainer';

// Mock the hook
vi.mock('../../hooks/useNotification', () => ({
  useNotificationStore: vi.fn(),
}));

describe('ToastContainer', () => {
  const mockRemove = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render nothing when there are no notifications', () => {
    (useNotificationStore as any).mockReturnValue({
      notifications: [],
      remove: mockRemove,
    });

    const { container } = render(<ToastContainer />);
    expect(container.firstChild).toBeNull();
  });

  it('should render notifications when they exist', () => {
    (useNotificationStore as any).mockReturnValue({
      notifications: [
        { id: '1', message: 'Hello', type: 'success' },
        { id: '2', message: 'Error', type: 'error' },
      ],
      remove: mockRemove,
    });

    render(<ToastContainer />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Error')).toBeInTheDocument();
  });

  it('should call remove when a toast is closed', () => {
    (useNotificationStore as any).mockReturnValue({
      notifications: [{ id: '1', message: 'Hello', type: 'success' }],
      remove: mockRemove,
    });

    render(<ToastContainer />);
    const closeBtn = screen.getByRole('button');
    fireEvent.click(closeBtn);

    expect(mockRemove).toHaveBeenCalledWith('1');
  });
});
