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
    render(<WeightLogDrawer {...mockProps} />);
    
    const weightInput = screen.getByTestId('weight-kg');
    const fatInput = screen.getByTestId('body-fat-pct');
    
    fireEvent.change(weightInput, { target: { value: '82.5' } });
    fireEvent.change(fatInput, { target: { value: '16.2' } });
    
    const saveBtn = screen.getByText(/Salvar/i);
    fireEvent.click(saveBtn);
    
    await waitFor(() => {
      expect(mockProps.onSubmit).toHaveBeenCalled();
      const submittedData = mockProps.onSubmit.mock.calls[0]![0];
      expect(submittedData.weight_kg).toBe(82.5);
      expect(submittedData.body_fat_pct).toBe(16.2);
    });
  });
});
