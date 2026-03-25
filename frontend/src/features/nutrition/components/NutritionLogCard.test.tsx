import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { NutritionLogCard } from './NutritionLogCard';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

const mockLog = {
  id: '1',
  user_email: 'test@test.com',
  date: '2024-01-01T12:00:00Z',
  calories: 2000,
  protein_grams: 150,
  carbs_grams: 200,
  fat_grams: 70,
} as any;

describe('NutritionLogCard', () => {
  it('should render nutrition details', () => {
    render(<NutritionLogCard log={mockLog} />);
    
    // Look for calories value "2,000" or "2.000" (toLocaleString)
    expect(screen.getByText(/2[.,]000/)).toBeInTheDocument();
    
    // Look for macros
    expect(screen.getByText(/150/)).toBeInTheDocument();
    expect(screen.getByText(/200/)).toBeInTheDocument();
    expect(screen.getByText(/70/)).toBeInTheDocument();
  });

  it('should call onDelete when delete button is clicked', () => {
    const onDelete = vi.fn();
    render(<NutritionLogCard log={mockLog} onDelete={onDelete} />);
    
    const deleteBtn = screen.getByLabelText(/Delete/i);
    fireEvent.click(deleteBtn);
    
    expect(onDelete).toHaveBeenCalledWith('1');
  });

  it('should call onClick when card is clicked', () => {
    const onClick = vi.fn();
    render(<NutritionLogCard log={mockLog} onClick={onClick} />);
    
    fireEvent.click(screen.getByTestId('nutrition-log-card'));
    expect(onClick).toHaveBeenCalledWith(mockLog);
  });
});
