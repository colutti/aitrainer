import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

interface MockAuthState {
  init: () => Promise<void> | void;
  isAuthenticated: boolean;
  loadUserInfo: () => Promise<void> | void;
}

const mockAuthState: MockAuthState = {
  init: vi.fn(),
  isAuthenticated: true,
  loadUserInfo: vi.fn(),
};

vi.mock('./shared/hooks/useAuth', () => ({
  useAuthStore: vi.fn((selector: (state: MockAuthState) => unknown) =>
    selector(mockAuthState)
  ),
}));

vi.mock('./AppRoutes', () => ({
  AppRoutes: () => (
    <div>
      <div data-testid="desktop-nav" />
      <div>App Routes</div>
    </div>
  ),
}));

vi.mock('./shared/components/ui/GlobalErrorBoundary', () => ({
  GlobalErrorBoundary: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('./shared/components/ui/ToastContainer', () => ({
  ToastContainer: () => <div>Toast Container</div>,
}));

vi.mock('./shared/components/ui/ConfirmationProvider', () => ({
  ConfirmationProvider: () => <div>Confirmation Provider</div>,
}));

import App from './App';

describe('App', () => {
  beforeEach(() => {
    mockAuthState.init = vi.fn();
    mockAuthState.isAuthenticated = true;
    mockAuthState.loadUserInfo = vi.fn();
  });

  it('initializes auth on mount and refreshes user info on focus', async () => {
    render(<App />);

    await waitFor(() => expect(mockAuthState.init).toHaveBeenCalledOnce());
    window.dispatchEvent(new Event('focus'));
    expect(mockAuthState.loadUserInfo).toHaveBeenCalledOnce();
  });

  it('renders authenticated route content inside the monochrome shell', async () => {
    render(<App />);

    expect(await screen.findByTestId('desktop-nav')).toBeInTheDocument();
  });
});
