import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { onboardingApi } from '../api/onboarding-api';

import { OnboardingPage } from './OnboardingPage';

vi.mock('../api/onboarding-api', () => ({
  onboardingApi: {
    validateToken: vi.fn(),
    completeOnboarding: vi.fn(),
  },
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
    const user = userEvent.setup();
    vi.mocked(onboardingApi.validateToken).mockResolvedValue({ valid: true, email: 'test@example.com' });
    vi.mocked(onboardingApi.completeOnboarding).mockResolvedValue({ token: 'new-token' });

    render(<OnboardingPage />);
    
    // Step 1: Password
    await screen.findByText('Criar Senha');
    const passInput = screen.getByPlaceholderText('Senha');
    const confirmInput = screen.getByPlaceholderText('Confirmar Senha');
    
    await user.type(passInput, 'Password123');
    await user.type(confirmInput, 'Password123');
    
    // Check validation match (assuming button becomes enabled or exists)
    const nextBtn = screen.getByRole('button', { name: /próximo/i });
    fireEvent.click(nextBtn);

    // Step 2: Profile
    expect(await screen.findByText('Seu Perfil')).toBeInTheDocument();
    // Fill profile
    await user.type(screen.getByLabelText(/idade/i), '25');
    await user.type(screen.getByLabelText(/peso/i), '70');
    await user.type(screen.getByLabelText(/altura/i), '175');
    
    fireEvent.click(screen.getByRole('button', { name: /próximo/i }));

    // Step 3: Trainer
    expect(await screen.findByText('Escolha seu Treinador')).toBeInTheDocument();
    // Select Atlas (default usually, or click one)
    const trainerCard = screen.getByText('Atlas');
    fireEvent.click(trainerCard);
    
    const finishBtn = screen.getByRole('button', { name: /finalizar/i });
    fireEvent.click(finishBtn);

    await waitFor(() => {
      expect(onboardingApi.completeOnboarding).toHaveBeenCalled();
      expect(window.location.href).toBe('http://localhost:3000/'); 
      // Since we mock navigate, we check navigation or logic call
    });
  });
});
