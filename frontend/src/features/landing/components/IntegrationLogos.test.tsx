import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { IntegrationLogos } from './IntegrationLogos';

describe('IntegrationLogos Component', () => {
  it('positions integrations as context input, not generic logos', () => {
    render(<IntegrationLogos />);

    expect(screen.getByText(/Traga sua rotina para dentro do sistema/i)).toBeInTheDocument();
    expect(screen.getByText(/Quanto mais contexto entra, mais útil fica a orientação/i)).toBeInTheDocument();
  });
});
