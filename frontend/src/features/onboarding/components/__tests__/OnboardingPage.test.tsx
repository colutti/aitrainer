import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useAuthStore } from '../../../../shared/hooks/useAuth';
import { OnboardingPage } from '../OnboardingPage';

// Mock translations
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

// Mock Auth Store
vi.mock('../../../../shared/hooks/useAuth', () => ({
  useAuthStore: vi.fn(),
}));

// Mock Onboarding API
vi.mock('../../api/onboarding-api', () => ({
  onboardingApi: {
    validateToken: vi.fn().mockResolvedValue({ valid: true, email: 'test@example.com' }),
  },
}));

const renderWithRouter = (ui: React.ReactElement) => {
  return render(ui, { wrapper: BrowserRouter });
};

describe('OnboardingPage - Step 2 (Profile)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Simulate user not onboarded yet
    (useAuthStore as any).mockReturnValue({
      userInfo: { email: 'test@example.com', onboarding_completed: false },
    });
  });

  it('disables "Next" button when profile fields are empty', async () => {
    renderWithRouter(<OnboardingPage />);
    
    // Wait for step 2 to be rendered (skipping step 0 and 1 due to userInfo mock)
    const nextButton = await screen.findByRole('button', { name: /onboarding\.next/i });
    expect(nextButton).toBeDisabled();
  });

  it('enables "Next" button when all required fields are filled', async () => {
    renderWithRouter(<OnboardingPage />);
    
    const ageInput = await screen.findByLabelText(/onboarding\.age/i);
    const weightInput = screen.getByLabelText(/body\.weight\.weight/i);
    const heightInput = screen.getByLabelText(/settings\.height/i);
    const nextButton = screen.getByRole('button', { name: /onboarding\.next/i });

    fireEvent.change(ageInput, { target: { value: '25' } });
    fireEvent.change(weightInput, { target: { value: '70' } });
    fireEvent.change(heightInput, { target: { value: '175' } });

    // gender defaults to 'male' translations in the component initial state or first click
    // Let's click a gender to be sure
    const maleButton = screen.getByRole('button', { name: /onboarding\.genders\.male/i });
    fireEvent.click(maleButton);

    await waitFor(() => {
      expect(nextButton).not.toBeDisabled();
    });
  });

  it('disables "Next" button if age is less than 18', async () => {
    renderWithRouter(<OnboardingPage />);
    
    const ageInput = await screen.findByLabelText(/onboarding\.age/i);
    const weightInput = screen.getByLabelText(/body\.weight\.weight/i);
    const heightInput = screen.getByLabelText(/settings\.height/i);
    const nextButton = screen.getByRole('button', { name: /onboarding\.next/i });

    fireEvent.change(ageInput, { target: { value: '17' } });
    fireEvent.change(weightInput, { target: { value: '70' } });
    fireEvent.change(heightInput, { target: { value: '175' } });

    expect(nextButton).toBeDisabled();
  });
});
