import { render, screen } from '../../utils/test-utils';

import { GlobalErrorBoundary } from './GlobalErrorBoundary';

function Thrower() {
  throw new Error('boom');
  return null;
}

describe('GlobalErrorBoundary', () => {
  it('renders the default fallback', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <GlobalErrorBoundary>
        <Thrower />
      </GlobalErrorBoundary>
    );

    expect(screen.getByText(/erro no servidor/i)).toBeInTheDocument();
    consoleError.mockRestore();
  });
});
