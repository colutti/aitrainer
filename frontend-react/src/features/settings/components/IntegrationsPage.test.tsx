import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import userEvent from '@testing-library/user-event';

import { integrationsApi } from '../api/integrations-api';
import { IntegrationsPage } from './IntegrationsPage';

vi.mock('../api/integrations-api', () => ({
  integrationsApi: {
    getHevyStatus: vi.fn(),
    saveHevyKey: vi.fn(),
    syncHevy: vi.fn(),
    getTelegramStatus: vi.fn(),
    generateTelegramCode: vi.fn(),
    uploadMfpCsv: vi.fn(),
    uploadZeppLifeCsv: vi.fn(),
  },
}));

describe('IntegrationsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render integrations status', async () => {
    vi.mocked(integrationsApi.getHevyStatus).mockResolvedValue({ enabled: true, hasKey: true, apiKeyMasked: '****123', lastSync: null });
    vi.mocked(integrationsApi.getTelegramStatus).mockResolvedValue({ connected: true, username: 'my_bot' });

    render(<IntegrationsPage />);

    expect(await screen.findByText(/Integração ativa. Chave: \*\*\*\*123/)).toBeInTheDocument();
    expect(await screen.findByText(/Conectado como @my_bot/)).toBeInTheDocument();
  });

  it('should save Hevy key', async () => {
    const user = userEvent.setup();
    vi.mocked(integrationsApi.getHevyStatus).mockResolvedValue({ enabled: false, hasKey: false, apiKeyMasked: null, lastSync: null });
    vi.mocked(integrationsApi.getTelegramStatus).mockResolvedValue({ connected: false });
    vi.mocked(integrationsApi.saveHevyKey).mockResolvedValue({ enabled: true, hasKey: true, apiKeyMasked: '****KEY', lastSync: null });

    render(<IntegrationsPage />);

    const input = await screen.findByLabelText(/API Key/i);
    await user.type(input, 'NEW_KEY');
    
    const saveBtn = screen.getByRole('button', { name: /salvar/i });
    fireEvent.click(saveBtn);

    await waitFor(() => {
        expect(integrationsApi.saveHevyKey).toHaveBeenCalledWith('NEW_KEY');
    });
  });

  it('should generate Telegram code', async () => {
    vi.mocked(integrationsApi.getHevyStatus).mockResolvedValue({ enabled: false, hasKey: false, apiKeyMasked: null, lastSync: null });
    vi.mocked(integrationsApi.getTelegramStatus).mockResolvedValue({ connected: false });
    vi.mocked(integrationsApi.generateTelegramCode).mockResolvedValue({ code: '123456', url: 'http://t.me/bot' });

    render(<IntegrationsPage />);

    const genBtn = await screen.findByText(/Gerar Código/);
    fireEvent.click(genBtn);

    expect(await screen.findByText('123456')).toBeInTheDocument();
  });
});
