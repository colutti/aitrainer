import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { NutritionLog } from '../../../shared/types/nutrition';

import { NutritionLogCard } from './NutritionLogCard';

describe('NutritionLogCard', () => {
  const mockLog: NutritionLog = {
    id: '1',
    date: '2024-01-01',
    calories: 2000,
    protein_grams: 150,
    carbs_grams: 200,
    fat_grams: 70,
    user_email: 'test@example.com',
    source: 'manual',
  };

  const mockOnDelete = vi.fn();

  it('should render log details', () => {
    render(
      <NutritionLogCard 
        log={mockLog} 
        onDelete={mockOnDelete} 
      />
    );

    // Look for calories value "2,000" (toLocaleString)
    expect(screen.getByText('2,000')).toBeInTheDocument();

    // Look for macros (toFixed(2))
    expect(screen.getByText('150.00')).toBeInTheDocument(); // Protein
    expect(screen.getByText('200.00')).toBeInTheDocument();  // Carbs
    expect(screen.getByText('70.00')).toBeInTheDocument();   // Fat
    
    // Check Date format (using regex or partial match if needed)
    // "01/01/2024" likely format for PT-BR
    // Let's assume formatDate renders something recognizable or check logic.
  });

  it('should trigger delete handler', () => {
    render(
      <NutritionLogCard 
        log={mockLog} 
        onDelete={mockOnDelete} 
      />
    );

    const deleteBtn = screen.getByTitle('Excluir registro');
    fireEvent.click(deleteBtn);
    
    expect(mockOnDelete).toHaveBeenCalledWith(mockLog.id);
  });
});
