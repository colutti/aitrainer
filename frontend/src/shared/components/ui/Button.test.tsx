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
    expect(document.querySelector('.animate-spin')).toBeInTheDocument();
  });

  it('should render primary buttons with the design-system token classes', () => {
    render(<Button>Save</Button>);
    const button = screen.getByRole('button', { name: 'Save' });

    expect(button).toHaveClass('bg-[color:var(--color-primary)]');
    expect(button).toHaveClass('text-[color:var(--color-on-primary)]');
    expect(button).toHaveClass('rounded-[var(--radius-md)]');
    expect(button).toHaveClass('focus-visible:ring-[color:var(--color-primary)]/20');
  });

  it('should keep button variants inside the shared surface language', () => {
    const { rerender } = render(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-[color:var(--color-surface-container-high)]');
    expect(screen.getByRole('button')).toHaveClass('border-[color:var(--color-outline-variant)]');

    rerender(<Button variant="ghost">Ghost</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-transparent');
    expect(screen.getByRole('button')).toHaveClass('text-[color:var(--color-on-surface-variant)]');

    rerender(<Button variant="danger">Danger</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-[color:var(--color-error)]');
    expect(screen.getByRole('button')).toHaveClass('text-[color:var(--color-on-error)]');
  });

  it('should apply size classes', () => {
    const { rerender } = render(<Button size="sm">Small</Button>);
    expect(screen.getByRole('button')).toHaveClass('h-9');

    rerender(<Button size="lg">Large</Button>);
    expect(screen.getByRole('button')).toHaveClass('h-12');
  });

  it('should apply fullWidth class', () => {
    render(<Button fullWidth>Full Width</Button>);
    expect(screen.getByRole('button')).toHaveClass('w-full');
  });

  it('should disable native mobile tap highlight color', () => {
    render(<Button>Tap safe</Button>);
    expect(screen.getByRole('button')).toHaveClass('[-webkit-tap-highlight-color:transparent]');
  });

  it('should use shared interaction state tokens', () => {
    const { rerender } = render(<Button>Primary</Button>);
    expect(screen.getByRole('button')).toHaveClass('hover:bg-[color:var(--color-primary-container)]');
    expect(screen.getByRole('button')).toHaveClass('active:translate-y-px');

    rerender(<Button variant="ghost">Ghost</Button>);
    expect(screen.getByRole('button')).toHaveClass('hover:bg-[color:var(--color-surface-container)]');
    expect(screen.getByRole('button')).toHaveClass('active:bg-[color:var(--color-surface-container-high)]');
  });
});
