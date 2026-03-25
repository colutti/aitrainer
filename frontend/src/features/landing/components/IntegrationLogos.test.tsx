import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { IntegrationLogos } from './IntegrationLogos';

describe('IntegrationLogos Component', () => {
  it('should render integration logos', () => {
    render(<IntegrationLogos />);
    expect(screen.getByText(/Ecossistema Aberto/i)).toBeInTheDocument();
  });
});
