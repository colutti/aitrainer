import { describe, it, expect, vi } from 'vitest';

import { render, screen, fireEvent, waitFor } from '../../../shared/utils/test-utils';

import { WeightLogDrawer } from './WeightLogDrawer';

describe('WeightLogDrawer', () => {
  const mockProps = {
    isOpen: true,
    onClose: vi.fn(),
    onSubmit: vi.fn().mockResolvedValue(undefined),
    log: null,
  };

  it('should render correct title for new log', () => {
    render(<WeightLogDrawer {...mockProps} />);
    expect(screen.getByText(/Registrar Peso/i)).toBeInTheDocument();
  });

  it('should render correct title for existing log', () => {
    const existingLog = {
      id: '1',
      user_email: 'user@example.com',
      date: '2024-01-01',
      weight_kg: 80,
      body_fat_pct: 15,
    };
    render(<WeightLogDrawer {...mockProps} log={existingLog} />);
    expect(screen.getByText(/Detalhes do Registro/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue('80')).toBeInTheDocument();
  });

  it('should call onSubmit with numeric values', async () => {
    const { container } = render(<WeightLogDrawer {...mockProps} />);
    
    const weightInput = screen.getByTestId('weight-kg');
    const dateInput = screen.getByLabelText(/Data/i);
    const compositionSummary = container.querySelector('details summary');
    if (!compositionSummary) throw new Error('Composition summary not found');
    fireEvent.click(compositionSummary);
    const measurementSummary = container.querySelectorAll('details summary')[1];
    if (!measurementSummary) throw new Error('Measurements summary not found');
    fireEvent.click(measurementSummary);

    const muscleKgInput = screen.getByLabelText(/Massa Muscular \(kg\)/i);
    const neckInput = screen.getByLabelText(/Pescoço/i);
    
    fireEvent.change(dateInput, { target: { value: '2026-04-01' } });
    fireEvent.change(weightInput, { target: { value: '82.5' } });
    fireEvent.change(muscleKgInput, { target: { value: '42.1' } });
    fireEvent.change(neckInput, { target: { value: '37' } });
    
    const saveBtn = screen.getByText(/Salvar/i);
    fireEvent.click(saveBtn);
    
    await waitFor(() => {
      expect(mockProps.onSubmit).toHaveBeenCalled();
      const submittedData = mockProps.onSubmit.mock.calls[0]![0];
      expect(submittedData.date).toBe('2026-04-01');
      expect(submittedData.weight_kg).toBe(82.5);
      expect(submittedData.body_fat_pct).toBeUndefined();
      expect(submittedData.muscle_mass_kg).toBe(42.1);
      expect(submittedData.neck_cm).toBe(37);
    });
  });

  it('should preload new fields when editing an existing log', () => {
    const existingLog = {
      id: '1',
      user_email: 'user@example.com',
      date: '2026-04-10',
      weight_kg: 80,
      body_fat_pct: 15,
      muscle_mass_kg: 40,
      neck_cm: 36,
    };

    render(<WeightLogDrawer {...mockProps} log={existingLog} />);

    expect(screen.getByLabelText(/Data/i)).toHaveValue('2026-04-10');
    expect(screen.getByLabelText(/Massa Muscular \(kg\)/i)).toHaveValue(40);
    expect(screen.getByLabelText(/Pescoço/i)).toHaveValue(36);
  });

  it('should keep advanced sections closed for new logs', () => {
    const { container } = render(<WeightLogDrawer {...mockProps} />);
    const expanded = container.querySelectorAll('details[open]');
    expect(expanded).toHaveLength(0);
  });

  it('should disable form controls in read-only mode', () => {
    const { container } = render(<WeightLogDrawer {...mockProps} isReadOnly />);

    expect(screen.getByTestId('weight-kg')).toBeDisabled();
    const compositionSummary = container.querySelector('details summary');
    if (!compositionSummary) throw new Error('Composition summary not found');
    fireEvent.click(compositionSummary);
    expect(screen.getByTestId('body-fat-pct')).toBeDisabled();
    expect(screen.getByRole('button', { name: /Salvar/i })).toBeDisabled();
    expect(screen.getByText('Demo Read-Only')).toBeInTheDocument();
  });
});
