import { describe, it, expect, vi } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { TrainerShowcase } from './TrainerShowcase';

const mockUsePublicConfig = vi.fn(() => ({
  enableNewUserSignups: true,
  isLoading: false,
  hasLoaded: true,
}));

vi.mock('../../../shared/hooks/usePublicConfig', () => ({
  usePublicConfig: () => mockUsePublicConfig(),
}));

describe('TrainerShowcase Component', () => {
  it('disables mentor CTA when signups are off', () => {
    mockUsePublicConfig.mockReturnValueOnce({
      enableNewUserSignups: false,
      isLoading: false,
      hasLoaded: true,
    });
    render(<TrainerShowcase />);

    expect(screen.getByRole('button', { name: /Começar com este mentor/i })).toBeDisabled();
  });

  it('presents mentors as coaching styles, not generic characters', () => {
    render(<TrainerShowcase />);

    expect(screen.getByText(/Escolha o estilo de acompanhamento que combina com você/i)).toBeInTheDocument();
    expect(screen.getAllByText('Atlas Prime').length).toBeGreaterThan(0);
    expect(screen.getByText('Luna Stardust')).toBeInTheDocument();
  });

  it('renders mentor specific CTA', () => {
    render(<TrainerShowcase />);

    expect(screen.getByRole('button', { name: /Começar com este mentor/i })).toBeInTheDocument();
  });

  it('defaults to Breno as selected mentor', () => {
    render(<TrainerShowcase />);

    expect(screen.getByText(/Constância, confiança e rotina sem peso excessivo/i)).toBeInTheDocument();
  });
});
