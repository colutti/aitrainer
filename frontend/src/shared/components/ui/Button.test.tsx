import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { Button } from './Button';

describe('Button', () => {
  it('should render children correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: /Click me/i })).toBeInTheDocument();
  });

  it('should handle click events', () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click me</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('should be disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('should be disabled when isLoading is true', () => {
    render(<Button isLoading>Click me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
    // Should show loading spinner div
    expect(document.querySelector('.animate-spin')).toBeInTheDocument();
  });

  it('should apply variant and size classes', () => {
    const { rerender } = render(<Button variant="danger" size="sm">Danger</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-red-500/10');
    expect(screen.getByRole('button')).toHaveClass('h-9');

    rerender(<Button variant="secondary" size="lg">Secondary</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-dark-card');
    expect(screen.getByRole('button')).toHaveClass('h-12');
  });

  it('should apply fullWidth class', () => {
    render(<Button fullWidth>Full Width</Button>);
    expect(screen.getByRole('button')).toHaveClass('w-full');
  });
});
