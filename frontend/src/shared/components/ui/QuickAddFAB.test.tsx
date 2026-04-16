import { vi } from 'vitest';

import { fireEvent, render, screen } from '../../utils/test-utils';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom'
  );
  return { ...actual, useNavigate: () => mockNavigate };
});

import { QuickAddFAB } from './QuickAddFAB';

describe('QuickAddFAB', () => {
  it('opens actions and navigates to the weight flow', () => {
    render(<QuickAddFAB />);

    expect(screen.getByTestId('quick-add-fab')).toHaveClass('bg-[color:var(--color-app-surface-raised)]');

    fireEvent.click(screen.getByTestId('quick-add-fab'));
    fireEvent.click(screen.getByRole('button', { name: /registrar peso/i }));

    expect(mockNavigate).toHaveBeenCalledWith(
      '/dashboard/body/weight?action=log-weight'
    );
  });
});
