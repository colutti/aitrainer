import { useForm } from 'react-hook-form';
import { describe, it, expect, vi } from 'vitest';

import { type NutritionFormData } from '../../../shared/types/nutrition';
import { render, screen } from '../../../shared/utils/test-utils';

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
    source: 'Manual' as const,
  };

  const defaultProps = {
    log: mockLog,
    isOpen: true,
    onClose: vi.fn(),
    mode: 'view' as const,
  };

  it('should render log details in view mode', () => {
    render(<NutritionLogDrawer {...defaultProps} />);
    
    expect(screen.getByText(/Detalhes da Refeição/i)).toBeInTheDocument();
    expect(screen.getByText('2000')).toBeInTheDocument();
    expect(screen.getByText('150g')).toBeInTheDocument();
    expect(screen.getByText('200g')).toBeInTheDocument();
    expect(screen.getByText('60g')).toBeInTheDocument();
  });

  const Wrapper = ({ onSubmit }: { onSubmit: (data: any) => Promise<void> }) => {
    const { register, control, handleSubmit, formState: { errors } } = useForm<NutritionFormData>();
    return (
      <NutritionLogDrawer
        {...defaultProps}
        mode="edit"
        register={register}
        control={control}
        errors={errors}
        handleSubmit={handleSubmit}
        onSubmit={onSubmit}
      />
    );
  };

  it('should render correctly in edit mode', () => {
    render(<Wrapper onSubmit={vi.fn()} />);
    
    expect(screen.getByText(/Editar Refeição/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Calorias/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Proteína/i)).toBeInTheDocument();
  });

  it('should return null if no log and not in edit mode', () => {
    const { container } = render(<NutritionLogDrawer {...defaultProps} log={null} />);
    expect(container.firstChild).toBeNull();
  });
});
