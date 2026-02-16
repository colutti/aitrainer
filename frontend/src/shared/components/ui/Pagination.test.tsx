import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';

import { Pagination } from './Pagination';

describe('Pagination', () => {
  const defaultProps = {
    currentPage: 1,
    totalPages: 5,
    onPageChange: vi.fn(),
  };

  it('renders correctly', () => {
    render(<Pagination {...defaultProps} />);

    expect(screen.getByText('1/5')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /anterior/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /próxima/i })).toBeInTheDocument();
  });

  it('does not render when totalPages <= 1', () => {
    const { container } = render(<Pagination {...defaultProps} totalPages={1} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('disables "Previous" button on first page', () => {
    render(<Pagination {...defaultProps} currentPage={1} />);
    expect(screen.getByRole('button', { name: /anterior/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /próxima/i })).not.toBeDisabled();
  });

  it('disables "Next" button on last page', () => {
    render(<Pagination {...defaultProps} currentPage={5} />);
    expect(screen.getByRole('button', { name: /anterior/i })).not.toBeDisabled();
    expect(screen.getByRole('button', { name: /próxima/i })).toBeDisabled();
  });

  it('calls onPageChange when buttons are clicked', () => {
    render(<Pagination {...defaultProps} currentPage={3} />);
    
    fireEvent.click(screen.getByRole('button', { name: /anterior/i }));
    expect(defaultProps.onPageChange).toHaveBeenCalledWith(2);
    
    fireEvent.click(screen.getByRole('button', { name: /próxima/i }));
    expect(defaultProps.onPageChange).toHaveBeenCalledWith(4);
  });
  
  it('disables buttons when isLoading is true', () => {
    render(<Pagination {...defaultProps} isLoading={true} currentPage={3} />);
    expect(screen.getByRole('button', { name: /anterior/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /próxima/i })).toBeDisabled();
  });
});
