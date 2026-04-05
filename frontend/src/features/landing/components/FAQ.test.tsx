import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { FAQ } from './FAQ';

describe('FAQ Component', () => {
  it('answers onboarding objections in the faq', () => {
    render(<FAQ />);

    expect(screen.getByText(/Preciso conectar apps para funcionar/i)).toBeInTheDocument();
  });
});
