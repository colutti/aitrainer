import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { MainLayout } from './MainLayout';

// Mock child components to avoid deep nesting issues
vi.mock('../ui/ToastContainer', () => ({ ToastContainer: () => <div data-testid="toast-container" /> }));
vi.mock('../ui/ConfirmationProvider', () => ({ ConfirmationProvider: ({ children }: any) => <div data-testid="confirmation-provider">{children}</div> }));
vi.mock('./Sidebar', () => ({ Sidebar: () => <div data-testid="sidebar" /> }));
vi.mock('./BottomNav', () => ({ BottomNav: () => <div data-testid="bottom-nav" /> }));

describe('MainLayout', () => {
  it('should render all layout components', () => {
    render(
      <MemoryRouter>
        <MainLayout />
      </MemoryRouter>
    );

    expect(screen.getByTestId('toast-container')).toBeInTheDocument();
    expect(screen.getByTestId('confirmation-provider')).toBeInTheDocument();
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('bottom-nav')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
  });
});
