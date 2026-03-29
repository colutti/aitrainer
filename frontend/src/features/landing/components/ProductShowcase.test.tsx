import { describe, it, expect } from 'vitest';

import esES from '../../../locales/es-ES.json';
import { render, screen } from '../../../shared/utils/test-utils';

import { ProductShowcase } from './ProductShowcase';

describe('ProductShowcase Component', () => {
  it('should render product features', () => {
    render(<ProductShowcase />);
    expect(screen.getByText(/Tudo em um só lugar/i)).toBeInTheDocument();
  });

  it('renders showcase labels driven by locale', () => {
    render(<ProductShowcase />);

    expect(screen.getByText(/peso 30 dias/i)).toBeInTheDocument();
    expect(screen.getByText(/ativ[ao] agora/i)).toBeInTheDocument();
  });

  it('keeps the spanish showcase and conversation locale contract complete', () => {
    expect(esES.landing.showcase.weight_30d).toBeTruthy();
    expect(esES.landing.showcase.active_now).toBeTruthy();
    expect(esES.landing.conversations.sofia.user_1).toBeTruthy();
    expect(esES.landing.conversations.sofia.trainer_1).toBeTruthy();
    expect(esES.landing.conversations.sofia.user_2).toBeTruthy();
    expect(esES.landing.conversations.gymbro.user_1).toBeTruthy();
    expect(esES.landing.conversations.gymbro.trainer_1).toBeTruthy();
    expect(esES.landing.conversations.gymbro.user_2).toBeTruthy();
  });
});
