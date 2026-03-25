import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { WeightLogCard } from './WeightLogCard';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      if (key === 'body.weight.body_fat') return 'Gordura';
      if (key === 'body.weight.muscle_mass') return 'Massa';
      if (key === 'shared.edit') return 'Editar registro';
      if (key === 'shared.delete') return 'Excluir registro';
      return key;
    },
  }),
}));

const mockLog = {
  id: '1',
  user_email: 'test@test.com',
  date: '2024-01-01T10:00:00Z',
  weight_kg: 80.5,
  body_fat_pct: 15.5,
  muscle_mass_kg: null,
  trend_weight: null,
  notes: 'Feeling good',
} as any;

describe('WeightLogCard', () => {
  it('should render log details', () => {
    render(<WeightLogCard log={mockLog} />);
    
    expect(screen.getByText(/01\/01\/2024/)).toBeInTheDocument();
    // Use regex for weight to handle formatting 80.5 or 80.50
    expect(screen.getByText(/80\.5/)).toBeInTheDocument();
    expect(screen.getByText(/15\.5/)).toBeInTheDocument();
    expect(screen.getByText(/"Feeling good"/i)).toBeInTheDocument();
  });

  it('should call onDelete when delete button is clicked', () => {
    const onDelete = vi.fn();
    render(<WeightLogCard log={mockLog} onDelete={onDelete} />);
    
    const deleteBtn = screen.getByLabelText(/Delete/i);
    fireEvent.click(deleteBtn);
    
    expect(onDelete).toHaveBeenCalledWith(mockLog.date);
  });

  it('should call onClick when card is clicked', () => {
    const onClick = vi.fn();
    render(<WeightLogCard log={mockLog} onClick={onClick} />);
    
    fireEvent.click(screen.getByTestId('weight-log-card'));
    expect(onClick).toHaveBeenCalledWith(mockLog);
  });
});
