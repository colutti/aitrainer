import { render, screen } from '@testing-library/react';
import { Search } from 'lucide-react';
import { describe, expect, it } from 'vitest';

import { Input } from './Input';

describe('Input', () => {
  it('should render label when provided', () => {
    render(<Input label="Username" id="user" />);
    expect(screen.getByLabelText(/Username/i)).toBeInTheDocument();
    expect(screen.getByText('Username')).toHaveClass('text-[13px]');
    expect(screen.getByText('Username')).toHaveClass('text-[color:var(--color-on-surface-variant)]');
  });

  it('should render error message when provided', () => {
    render(<Input error="Invalid input" />);
    expect(screen.getByText(/Invalid input/i)).toBeInTheDocument();
    expect(screen.getByText(/Invalid input/i)).toHaveClass('text-[color:var(--color-error)]');
  });

  it('should render left icon when provided', () => {
    render(<Input leftIcon={<Search data-testid="search-icon" />} />);
    expect(screen.getByTestId('search-icon')).toBeInTheDocument();
  });

  it('should use shared icon state tokens', () => {
    render(<Input leftIcon={<Search data-testid="search-icon" />} />);
    const iconWrapper = screen.getByTestId('search-icon').parentElement;
    expect(iconWrapper).toHaveClass('text-[color:var(--color-on-surface-variant)]');
    expect(iconWrapper).toHaveClass('group-focus-within:text-[color:var(--color-primary)]');
  });

  it('should render inputs with the shared field surface classes', () => {
    render(<Input aria-label="Name" />);
    const input = screen.getByRole('textbox');

    expect(input).toHaveClass('border-[color:var(--color-outline-variant)]');
    expect(input).toHaveClass('bg-[color:var(--color-surface-container-low)]');
    expect(input).toHaveClass('rounded-[var(--radius-md)]');
    expect(input).toHaveClass('focus-visible:border-[color:var(--color-primary)]');
  });

  it('should apply error classes to input', () => {
    render(<Input error="error" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('border-[color:var(--color-error)]');
    expect(input).toHaveClass('focus-visible:ring-[color:var(--color-error)]/20');
  });

  it('should apply custom className', () => {
    render(<Input className="custom-input" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('custom-input');
  });

  it('should be disabled when disabled prop is true', () => {
    render(<Input disabled />);
    expect(screen.getByRole('textbox')).toBeDisabled();
  });
});
