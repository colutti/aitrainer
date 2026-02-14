import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { WeightLog } from '../../../shared/types/body';

import { WeightLogDrawer } from './WeightLogDrawer';

describe('WeightLogDrawer', () => {
  const mockLog: WeightLog = {
    id: '1',
    date: '2024-01-01',
    weight_kg: 80.5,
    trend_weight: 81.0, // Trend down
    body_fat_pct: 15.5,
    muscle_mass_pct: 40.0,
    bmr: 1800,
    visceral_fat: 5,
    neck_cm: 40,
    waist_cm: 80,
    user_email: 'test@example.com',
    notes: 'Feeling good',
  };

  const mockOnClose = vi.fn();

  it('should not render when log is null', () => {
    const { container } = render(
      <WeightLogDrawer log={null} isOpen={true} onClose={mockOnClose} />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('should render content when open', () => {
    render(
      <WeightLogDrawer log={mockLog} isOpen={true} onClose={mockOnClose} />
    );

    // Header
    expect(screen.getByText('Detalhes do Registro')).toBeInTheDocument();
    
    // Weight
    expect(screen.getByText('80.50')).toBeInTheDocument();
    expect(screen.getByText('kg')).toBeInTheDocument();

    // Trend
    expect(screen.getByText('Tendência')).toBeInTheDocument();
    // 81.0 - 80.5 = 0.5. diff is 0.5. Arrow ▼ because 80.5 < 81.0 (Down)
    // "0.50kg" or similar.
    // Text might be split: "▼" "0.50kg".
    // Let's check for "0.50kg" text content presence or loosely.
    expect(screen.getByText(/0.50kg/)).toBeInTheDocument();

    // Composition
    expect(screen.getByText('15.5%')).toBeInTheDocument(); // Fat
    expect(screen.getByText('40%')).toBeInTheDocument();   // Muscle

    // Measurements
    expect(screen.getByText('Pescoço')).toBeInTheDocument();
    expect(screen.getByText('40')).toBeInTheDocument();

    // Notes
    expect(screen.getByText(/"Feeling good"/)).toBeInTheDocument();
  });

  it('should trigger onClose when close button clicked', () => {
    render(
      <WeightLogDrawer log={mockLog} isOpen={true} onClose={mockOnClose} />
    );

    // Close button (X icon)
    // Finding button by hierarchy or assuming it's a button.
    // The drawer has a close button in header.
    const closeButtons = screen.getAllByRole('button');
    if (closeButtons[0]) fireEvent.click(closeButtons[0]);
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should trigger onClose when backdrop clicked', () => {
    const { container } = render(
      <WeightLogDrawer log={mockLog} isOpen={true} onClose={mockOnClose} />
    );
    
    // Backdrop is the first div.
    // We can find by class name check or just first child.
    // <div className="fixed inset-0 ..." onClick={onClose} />
    // It has `fixed inset-0`.
    const backdrop = container.firstChild as HTMLElement;
    fireEvent.click(backdrop);
    expect(mockOnClose).toHaveBeenCalled();
  });
});
