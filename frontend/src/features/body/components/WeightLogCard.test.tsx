import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { WeightLog } from '../../../shared/types/body';

import { WeightLogCard } from './WeightLogCard';

describe('WeightLogCard', () => {
  const mockLog: WeightLog = {
    id: '1',
    date: '2024-01-01',
    weight_kg: 80.5,
    body_fat_pct: 15.5,
    user_email: 'user@example.com',
  };

  const mockOnDelete = vi.fn();
  const mockOnEdit = vi.fn();
  const mockOnClick = vi.fn();

  it('should render log details', () => {
    render(
      <WeightLogCard 
        log={mockLog} 
        onDelete={mockOnDelete} 
        onEdit={mockOnEdit} 
        onClick={mockOnClick}
      />
    );

    expect(screen.getByText('80.50')).toBeInTheDocument();
    expect(screen.getByText('15.5')).toBeInTheDocument();
    // Helper function formats date, check if date part is present or mock format if needed. 
    // Assuming standard format or checking specific text if format is known.
    // "2024-01-01" might be formatted. Let's check for date/month presence if needed, or loosely check.
    // Actually, `formatDate` from utils is likely used.
  });

  it('should trigger click handlers', () => {
    render(
      <WeightLogCard 
        log={mockLog} 
        onDelete={mockOnDelete} 
        onEdit={mockOnEdit} 
        onClick={mockOnClick}
      />
    );

    // Main Card click
    screen.getByText('80.50').closest('div'); // A bit loose but valid if closest div is clickable
    // The closest div might be deep in the card.

    // The whole card has the onClick. Let's find the card container.
    // The card container has `cursor-pointer`.
    // Or we can just click "80.50" directly, as event bubbles up.
    
    // Let's fire click on "80.50"
    fireEvent.click(screen.getByText('80.50'));
    // Wait, the card structure:
    /*
      <div onClick={() => onClick?.(log)} ...>
        ...
        <span>80.50 ...</span>
    */
    // Clicking child triggers parent onClick.
    expect(mockOnClick).toHaveBeenCalledWith(mockLog);
  });
  
  it('should trigger delete and edit', () => {
     render(
      <WeightLogCard 
        log={mockLog} 
        onDelete={mockOnDelete} 
        onEdit={mockOnEdit} 
        onClick={mockOnClick}
      />
    );
      
    const editBtn = screen.getByTitle('Editar registro');
    fireEvent.click(editBtn);
    expect(mockOnEdit).toHaveBeenCalledWith(mockLog);
    
    const deleteBtn = screen.getByTitle('Excluir registro');
    fireEvent.click(deleteBtn);
    expect(mockOnDelete).toHaveBeenCalledWith(mockLog.date);
  });
});
