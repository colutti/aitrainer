import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { BottomNav } from './BottomNav';

describe('BottomNav', () => {
  it('should render mobile navigation links', () => {
    render(
      <MemoryRouter>
        <BottomNav />
      </MemoryRouter>
    );

    // Check for some key icons or labels (BottomNav might use only icons or small labels)
    expect(screen.getByTestId('nav-home')).toBeInTheDocument();
    expect(screen.getByTestId('nav-workouts')).toBeInTheDocument();
    expect(screen.getByTestId('nav-nutrition')).toBeInTheDocument();
  });
});
