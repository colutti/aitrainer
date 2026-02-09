import { render, screen } from '@testing-library/react';
import { Search } from 'lucide-react';
import { describe, expect, it } from 'vitest';

import { Input } from './Input';

describe('Input', () => {
  it('should render label when provided', () => {
    render(<Input label="Username" id="user" />);
    expect(screen.getByLabelText(/Username/i)).toBeInTheDocument();
  });

  it('should render error message when provided', () => {
    render(<Input error="Invalid input" />);
    expect(screen.getByText(/Invalid input/i)).toBeInTheDocument();
  });

  it('should render left icon when provided', () => {
    render(<Input leftIcon={<Search data-testid="search-icon" />} />);
    expect(screen.getByTestId('search-icon')).toBeInTheDocument();
  });

  it('should apply error classes to input', () => {
    render(<Input error="error" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('border-red-500');
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
