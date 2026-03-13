import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { onboardingApi } from '../api/onboarding-api';

import { OnboardingPage } from './OnboardingPage';

vi.mock('../api/onboarding-api', () => ({
  onboardingApi: {
    validateToken: vi.fn(),
    completeOnboarding: vi.fn(),
  },
}));

// Mock Firebase
vi.mock('../../../features/auth/firebase', () => ({
  auth: {},
}));

vi.mock('firebase/auth', () => ({
  createUserWithEmailAndPassword: vi.fn().mockResolvedValue({
    user: {
      getIdToken: vi.fn().mockResolvedValue('fake-firebase-token'),
    },
  }),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  useSearchParams: () => [new URLSearchParams({ token: 'abc-123' })],
}));

describe('OnboardingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should validate token on mount', async () => {
    vi.mocked(onboardingApi.validateToken).mockResolvedValue({ valid: true, email: 'test@example.com' });
    
    render(<OnboardingPage />);
    
    expect(await screen.findByText('Criar Senha')).toBeInTheDocument();
    expect(onboardingApi.validateToken).toHaveBeenCalledWith('abc-123');
  });

  it('should show error if token invalid', async () => {
    vi.mocked(onboardingApi.validateToken).mockResolvedValue({ valid: false, reason: 'expired' });
    
    render(<OnboardingPage />);
    
    expect(await screen.findByText(/expirou/i)).toBeInTheDocument();
  });

  it('should navigate through steps and submit', async () => {
    vi.mocked(onboardingApi.validateToken).mockResolvedValue({ valid: true, email: 'test@example.com' });
    vi.mocked(onboardingApi.completeOnboarding).mockResolvedValue({ token: 'new-token' });

    const { container } = render(<OnboardingPage />);
    
    // Step 1: Password
    await screen.findByText('Criar Senha');
    const passInput = container.querySelector('#password')!;
    const confirmInput = container.querySelector('#confirmPassword')!;
    
    fireEvent.change(passInput, { target: { value: 'Password123' } });
    fireEvent.change(confirmInput, { target: { value: 'Password123' } });
    
    // Check validation match (assuming button becomes enabled or exists)
    const nextBtn = screen.getByRole('button', { name: /próximo/i });
    fireEvent.click(nextBtn);

    // Step 2: Profile
    expect(await screen.findByText('Seu Perfil')).toBeInTheDocument();
    // Select Gender
    fireEvent.click(screen.getByText('Masculino'));
    // Fill profile
    fireEvent.change(screen.getByLabelText(/idade/i), { target: { value: '25' } });
    fireEvent.change(screen.getByLabelText(/peso/i), { target: { value: '70' } });
    fireEvent.change(screen.getByLabelText(/altura/i), { target: { value: '175' } });
    
    fireEvent.click(screen.getByRole('button', { name: /próximo/i }));

    // Step 3: Plan
    expect(await screen.findByText('Escolha seu Plano')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Free'));
    fireEvent.click(screen.getByRole('button', { name: /próximo/i }));

    // Step 4: Trainer
    expect(await screen.findByText('Escolha seu Treinador')).toBeInTheDocument();
    const trainerCard = screen.getByText('GymBro');
    fireEvent.click(trainerCard);
    
    // Agora o botão é "Próximo" para ir para Integrações
    const nextToIntegrationsBtn = screen.getByRole('button', { name: /próximo/i });
    fireEvent.click(nextToIntegrationsBtn);

    // Passo adicional: Integrações
    expect(await screen.findByText(/Turbine sua Evolução/i)).toBeInTheDocument();
    const finishBtn = screen.getByRole('button', { name: /finalizar/i });
    fireEvent.click(finishBtn);

    await waitFor(() => {
      expect(onboardingApi.completeOnboarding).toHaveBeenCalled();
      expect(screen.getByText(/Tudo Pronto/i)).toBeInTheDocument();
    });
  });

  it('should allow selecting Pro plan and send it to API', async () => {
    vi.mocked(onboardingApi.validateToken).mockResolvedValue({ valid: true, email: 'test@example.com' });
    vi.mocked(onboardingApi.completeOnboarding).mockResolvedValue({ token: 'new-token' });

    const { container } = render(<OnboardingPage />);
    
    // Step 1: Password
    await screen.findByText('Criar Senha');
    fireEvent.change(container.querySelector('#password')!, { target: { value: 'Password123' } });
    fireEvent.change(container.querySelector('#confirmPassword')!, { target: { value: 'Password123' } });
    fireEvent.click(screen.getByRole('button', { name: /próximo/i }));

    // Step 2: Profile
    expect(await screen.findByText('Seu Perfil')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Masculino'));
    fireEvent.change(screen.getByLabelText(/idade/i), { target: { value: '30' } });
    fireEvent.change(screen.getByLabelText(/peso/i), { target: { value: '80' } });
    fireEvent.change(screen.getByLabelText(/altura/i), { target: { value: '180' } });
    fireEvent.click(screen.getByRole('button', { name: /próximo/i }));

    // Step 3: Plan - Select Pro instead of Free
    expect(await screen.findByText('Escolha seu Plano')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Pro'));
    fireEvent.click(screen.getByRole('button', { name: /próximo/i }));

    // Step 4: Trainer - Atlas should be unlocked
    expect(await screen.findByText('Escolha seu Treinador')).toBeInTheDocument();
    const atlasCard = screen.getByText('Atlas');
    // Ensure it's not disabled (in this component we don't use 'disabled' attribute on buttons but we check logic)
    fireEvent.click(atlasCard);
    fireEvent.click(screen.getByRole('button', { name: /próximo/i }));

    // Step 5: Integrations
    expect(await screen.findByText(/Turbine sua Evolução/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /finalizar/i }));

    await waitFor(() => {
      expect(onboardingApi.completeOnboarding).toHaveBeenCalledWith(expect.objectContaining({
        subscription_plan: 'Pro',
        trainer_type: 'atlas'
      }));
    });
  });
});
