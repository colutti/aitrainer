import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { useAdminAuthStore } from '../hooks/useAdminAuth';

import { AdminProtectedRoute } from './AdminProtectedRoute';

vi.mock('../hooks/useAdminAuth', () => ({ useAdminAuthStore: vi.fn() }));

describe('AdminProtectedRoute', () => {
  it('redirects unauthenticated users to /login', () => {
    vi.mocked(useAdminAuthStore).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
    } as never);

    render(
      <MemoryRouter initialEntries={['/private']}>
        <Routes>
          <Route
            path="/private"
            element={
              <AdminProtectedRoute>
                <div>secret</div>
              </AdminProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Login Screen</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.queryByText('secret')).not.toBeInTheDocument();
    expect(screen.getByText('Login Screen')).toBeInTheDocument();
  });
});
