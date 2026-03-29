import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { IntegrationLogos } from './IntegrationLogos';

describe('IntegrationLogos Component', () => {
  it('should render integration logos', () => {
    render(<IntegrationLogos />);
    expect(screen.getByText(/Ecossistema Aberto/i)).toBeInTheDocument();
  });

  it('shows integrations as available instead of coming soon', () => {
    render(<IntegrationLogos />);

    expect(screen.queryByText(/em breve/i)).not.toBeInTheDocument();
    expect(screen.getAllByText(/dispon[ií]vel/i)).toHaveLength(3);
  });
});
