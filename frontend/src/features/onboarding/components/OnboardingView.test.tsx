import { describe, it, expect, vi } from 'vitest';

import { render, screen, fireEvent } from '../../../shared/utils/test-utils';

import { OnboardingView } from './OnboardingView';

describe('OnboardingView', () => {
  const mockProps = {
    step: 2,
    onNext: vi.fn(),
    onBack: vi.fn(),
    onSubmit: vi.fn(),
    onFinish: vi.fn(),
    formData: {
      name: 'Test User',
      gender: 'Masculino',
      age: 25,
      height: 180,
      weight: 80,
      goal_type: 'maintain',
      trainer_type: 'gymbro',
      subscription_plan: 'Free'
    },
    setFormData: vi.fn(),
    loading: false,
    email: 'test@example.com',
    hevyApiKey: '',
    setHevyApiKey: vi.fn(),
    onHevyConnect: vi.fn(),
    connectingHevy: false,
    onUpload: vi.fn(),
    importing: null,
  };

  it('should render Step 2 (Profile) correctly', () => {
    render(<OnboardingView {...mockProps} step={2} />);
    
    expect(screen.getByText(/Seu Perfil/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test User')).toBeInTheDocument();
    expect(screen.getByDisplayValue('25')).toBeInTheDocument();
    
    const nextBtn = screen.getByText(/Próximo/i);
    expect(nextBtn).toBeEnabled();
    fireEvent.click(nextBtn);
    expect(mockProps.onNext).toHaveBeenCalled();
  });

  it('should disable Next button in Step 2 if fields are missing', () => {
    const incompleteProps = {
      ...mockProps,
      formData: { ...mockProps.formData, name: '' }
    };
    render(<OnboardingView {...incompleteProps} step={2} />);
    
    const nextBtn = screen.getByText(/Próximo/i);
    expect(nextBtn).toBeDisabled();
  });

  it('should render Step 3 (Plan) correctly', () => {
    render(<OnboardingView {...mockProps} step={3} />);
    
    expect(screen.getByText(/Plano de Jornada/i)).toBeInTheDocument();
    expect(screen.getByText('Free')).toBeInTheDocument();
    expect(screen.getByText('Basic')).toBeInTheDocument();
    expect(screen.getByText('Pro')).toBeInTheDocument();
    expect(screen.queryByText('Premium')).not.toBeInTheDocument();
    
    const nextBtn = screen.getByText(/Próximo/i);
    fireEvent.click(nextBtn);
    expect(mockProps.onNext).toHaveBeenCalled();
  });

  it('should persist selected plan when user chooses pro on Step 3', () => {
    render(<OnboardingView {...mockProps} step={3} />);

    const proAction = screen.getByRole('button', { name: /Assinar Pro/i });
    fireEvent.click(proAction);

    expect(mockProps.setFormData).toHaveBeenCalledWith(
      expect.objectContaining({ subscription_plan: 'Pro' })
    );
  });

  it('should render Step 4 (Trainer) correctly', () => {
    render(<OnboardingView {...mockProps} step={4} />);
    
    expect(screen.getByText(/Seu Mentor/i)).toBeInTheDocument();
    expect(screen.getByText('Atlas')).toBeInTheDocument();
    expect(screen.getByText('GymBro')).toBeInTheDocument();
    
    const nextBtn = screen.getByText(/Próximo/i);
    fireEvent.click(nextBtn);
    expect(mockProps.onSubmit).toHaveBeenCalled();
  });

  it('should render Step 5 (Integrations) correctly', () => {
    render(<OnboardingView {...mockProps} step={5} />);
    
    expect(screen.getByText(/Conectar Apps/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Hevy API Key/i)).toBeInTheDocument();
    
    const finishBtn = screen.getByText(/Finalizar/i);
    fireEvent.click(finishBtn);
    expect(mockProps.onNext).toHaveBeenCalled();
  });

  it('should render Step 6 (Success) correctly', () => {
    render(<OnboardingView {...mockProps} step={6} />);
    
    expect(screen.getByText(/Bem-vindo!/i)).toBeInTheDocument();
    
    const goDashBtn = screen.getByText(/Ir para Dashboard/i);
    fireEvent.click(goDashBtn);
    expect(mockProps.onFinish).toHaveBeenCalled();
  });
});
