import { describe, it, expect, vi } from 'vitest';

import { fireEvent, render, screen, waitFor } from '../../../shared/utils/test-utils';

import { NutritionLogDrawer } from './NutritionLogDrawer';

describe('NutritionLogDrawer', () => {
  const mockLog = {
    id: '1',
    user_email: 'user@example.com',
    date: '2024-01-01',
    calories: 2000,
    protein_grams: 150,
    carbs_grams: 200,
    fat_grams: 60,
    fiber_grams: 28,
    sodium_mg: 1800,
    source: 'Manual' as const,
  };

  const defaultProps = {
    log: mockLog,
    isOpen: true,
    onClose: vi.fn(),
    onSubmit: vi.fn(),
    mode: 'view' as const,
  };

  it('should render log details in view mode', () => {
    render(<NutritionLogDrawer {...defaultProps} />);
    
    expect(screen.getByText(/Detalhes/i)).toBeInTheDocument();
    expect(screen.getByText('2000')).toBeInTheDocument();
    expect(screen.getByText('150g')).toBeInTheDocument();
    expect(screen.getByText('200g')).toBeInTheDocument();
    expect(screen.getByText('60g')).toBeInTheDocument();
  });

  it('should render correctly in edit mode', () => {
    render(<NutritionLogDrawer {...defaultProps} mode="edit" />);
    
    expect(screen.getByText(/Refeição/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Data/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Calorias/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Proteína/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Fibra/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Sódio/i)).toBeInTheDocument();
  });

  it('should submit fiber and sodium fields', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<NutritionLogDrawer {...defaultProps} mode="edit" log={null} onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText(/Calorias/i), { target: { value: '2200' } });
    fireEvent.change(screen.getByLabelText(/Proteína/i), { target: { value: '170' } });
    fireEvent.change(screen.getByLabelText(/Carboidratos/i), { target: { value: '210' } });
    fireEvent.change(screen.getByLabelText(/Gordura/i), { target: { value: '70' } });
    fireEvent.change(screen.getByLabelText(/Fibra/i), { target: { value: '30' } });
    fireEvent.change(screen.getByLabelText(/Sódio/i), { target: { value: '2000' } });

    fireEvent.click(screen.getByRole('button', { name: /Salvar/i }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
        fiber_grams: 30,
        sodium_mg: 2000,
      }));
    });
  });

  it('should force view mode in read-only state', () => {
    render(<NutritionLogDrawer {...defaultProps} mode="edit" isReadOnly />);

    expect(screen.getByText(/Detalhes/i)).toBeInTheDocument();
    expect(screen.getByText('Demo Read-Only')).toBeInTheDocument();
    expect(screen.queryByLabelText(/Calorias/i)).not.toBeInTheDocument();
  });

  it('should return null if no log and not in edit mode', () => {
    const { container } = render(<NutritionLogDrawer {...defaultProps} log={null} />);
    expect(container.firstChild).toBeNull();
  });
});
