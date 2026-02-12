import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useNotificationStore } from '../../../shared/hooks/useNotification';
import { integrationsApi } from '../api/integrations-api';

import { IntegrationsPage } from './IntegrationsPage';

vi.mock('../api/integrations-api', () => ({
  integrationsApi: {
    getHevyStatus: vi.fn(),
    saveHevyKey: vi.fn(),
    removeHevyKey: vi.fn(),
    syncHevy: vi.fn(),
    getWebhookConfig: vi.fn(),
    generateWebhook: vi.fn(),
    revokeWebhook: vi.fn(),
    getTelegramStatus: vi.fn(),
    generateTelegramCode: vi.fn(),
    uploadMfpCsv: vi.fn(),
    uploadZeppLifeCsv: vi.fn(),
  },
}));

vi.mock('../../../shared/hooks/useNotification', () => ({
  useNotificationStore: vi.fn(),
}));

describe('IntegrationsPage', () => {
  const mockNotify = {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useNotificationStore as any).mockReturnValue(mockNotify);
  });

  const setupMocks = () => {
    vi.mocked(integrationsApi.getHevyStatus).mockResolvedValue({ enabled: false, hasKey: false, apiKeyMasked: null, lastSync: null });
    vi.mocked(integrationsApi.getTelegramStatus).mockResolvedValue({ connected: false });
    vi.mocked(integrationsApi.getWebhookConfig).mockResolvedValue({ hasWebhook: false, webhookUrl: null, authHeader: null });
  };

  it('should render integrations status', async () => {
    vi.mocked(integrationsApi.getHevyStatus).mockResolvedValue({ enabled: true, hasKey: true, apiKeyMasked: '****123', lastSync: '2024-01-01T10:00:00Z' });
    vi.mocked(integrationsApi.getTelegramStatus).mockResolvedValue({ connected: true, username: 'my_bot' });

    render(<IntegrationsPage />);

    expect(await screen.findByText(/Integração ativa. Chave: \*\*\*\*123/)).toBeInTheDocument();
    expect(await screen.findByText(/Conectado como @my_bot/)).toBeInTheDocument();
  });

  it('should save Hevy key successfully', async () => {
    const user = userEvent.setup();
    setupMocks();
    vi.mocked(integrationsApi.saveHevyKey).mockResolvedValue({ enabled: true, hasKey: true, apiKeyMasked: '****KEY', lastSync: null });

    render(<IntegrationsPage />);

    const input = await screen.findByLabelText(/API Key/i);
    await user.type(input, 'NEW_KEY');
    
    const saveBtn = screen.getByRole('button', { name: /salvar/i });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(integrationsApi.saveHevyKey).toHaveBeenCalledWith('NEW_KEY');
      expect(mockNotify.success).toHaveBeenCalledWith('Chave da Hevy salva com sucesso!');
    });
  });

  it('should sync Hevy successfully', async () => {
    vi.mocked(integrationsApi.getHevyStatus).mockResolvedValue({ enabled: true, hasKey: true, apiKeyMasked: '****123', lastSync: null });
    vi.mocked(integrationsApi.getTelegramStatus).mockResolvedValue({ connected: false });
    vi.mocked(integrationsApi.getWebhookConfig).mockResolvedValue({ hasWebhook: false, webhookUrl: null, authHeader: null });
    vi.mocked(integrationsApi.syncHevy).mockResolvedValue({ imported: 5, skipped: 0 });

    render(<IntegrationsPage />);

    const syncBtn = await screen.findByText(/Sincronizar Agora/);
    fireEvent.click(syncBtn);

    await waitFor(() => {
      expect(integrationsApi.syncHevy).toHaveBeenCalled();
      expect(mockNotify.success).toHaveBeenCalledWith(expect.stringContaining('Importados: 5'));
    });
  });

  it('should remove Hevy key via backend', async () => {
    vi.mocked(integrationsApi.getHevyStatus)
      .mockResolvedValueOnce({ enabled: true, hasKey: true, apiKeyMasked: '****123', lastSync: null });
    vi.mocked(integrationsApi.getTelegramStatus).mockResolvedValue({ connected: false });
    vi.mocked(integrationsApi.getWebhookConfig).mockResolvedValue({ hasWebhook: false, webhookUrl: null, authHeader: null });
    vi.mocked(integrationsApi.removeHevyKey).mockResolvedValue({ enabled: false, hasKey: false, apiKeyMasked: null, lastSync: null });

    render(<IntegrationsPage />);

    const removeBtn = await screen.findByText(/Remover/);
    fireEvent.click(removeBtn);

    await waitFor(() => {
      expect(integrationsApi.removeHevyKey).toHaveBeenCalled();
      expect(screen.getByLabelText(/API Key/i)).toBeInTheDocument();
    });
  });

  it('should handle uploads (MFP)', async () => {
    setupMocks();
    vi.mocked(integrationsApi.uploadMfpCsv).mockResolvedValue({ created: 10, updated: 5, errors: 0, total_days: 7, error_messages: [] });

    render(<IntegrationsPage />);

    const fileInputs = document.querySelectorAll('input[type="file"]');
    const mfpInput = fileInputs[0]!; // Based on DOM order in the component
    
    const file = new File(['test'], 'mfp.csv', { type: 'text/csv' });
    fireEvent.change(mfpInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(integrationsApi.uploadMfpCsv).toHaveBeenCalledWith(file);
      expect(mockNotify.success).toHaveBeenCalledWith(expect.stringContaining('Criados: 10'));
    });
  });

  it('should handle uploads (Zepp)', async () => {
    setupMocks();
    vi.mocked(integrationsApi.uploadZeppLifeCsv).mockResolvedValue({ created: 5, updated: 2, errors: 1, total_days: 7, error_messages: ['Error row 1'] });

    render(<IntegrationsPage />);

    const fileInputs = document.querySelectorAll('input[type="file"]');
    const zeppInput = fileInputs[1]!;
    
    const file = new File(['test'], 'zepp.csv', { type: 'text/csv' });
    fireEvent.change(zeppInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(integrationsApi.uploadZeppLifeCsv).toHaveBeenCalledWith(file);
      expect(mockNotify.info).toHaveBeenCalledWith(expect.stringContaining('1 erros encontrados'));
    });
  });

  it('should handle errors in Telegram generation', async () => {
    setupMocks();
    vi.mocked(integrationsApi.generateTelegramCode).mockRejectedValue(new Error('fail'));

    render(<IntegrationsPage />);

    const genBtn = await screen.findByText(/Gerar Código/);
    fireEvent.click(genBtn);

    await waitFor(() => {
      expect(mockNotify.error).toHaveBeenCalledWith('Erro ao gerar código do Telegram.');
    });
  });

  it('should display webhook configuration when available', async () => {
    vi.mocked(integrationsApi.getHevyStatus).mockResolvedValue({ enabled: true, hasKey: true, apiKeyMasked: '****123', lastSync: null });
    vi.mocked(integrationsApi.getTelegramStatus).mockResolvedValue({ connected: false });
    vi.mocked(integrationsApi.getWebhookConfig).mockResolvedValue({
      hasWebhook: true,
      webhookUrl: 'https://example.com/webhook/token123',
      authHeader: 'Bearer ****abcd',
    });

    render(<IntegrationsPage />);

    expect(await screen.findByText(/Webhook para Sincronização Automática/i)).toBeInTheDocument();
    expect(await screen.findByText(/example.com\/webhook\/token123/)).toBeInTheDocument();
  });

  it('should generate webhook credentials', async () => {
    vi.mocked(integrationsApi.getHevyStatus).mockResolvedValue({ enabled: true, hasKey: true, apiKeyMasked: '****123', lastSync: null });
    vi.mocked(integrationsApi.getTelegramStatus).mockResolvedValue({ connected: false });
    vi.mocked(integrationsApi.getWebhookConfig).mockResolvedValueOnce({ hasWebhook: false, webhookUrl: null, authHeader: null });
    vi.mocked(integrationsApi.generateWebhook).mockResolvedValue({
      webhookUrl: 'https://example.com/webhook/new',
      authHeader: 'Bearer full_secret',
    });
    vi.mocked(integrationsApi.getWebhookConfig).mockResolvedValueOnce({
      hasWebhook: true,
      webhookUrl: 'https://example.com/webhook/new',
      authHeader: 'Bearer ****cret',
    });

    render(<IntegrationsPage />);

    const configBtn = await screen.findByText(/Configurar Webhook/);
    fireEvent.click(configBtn);

    await waitFor(() => {
      expect(integrationsApi.generateWebhook).toHaveBeenCalled();
      expect(mockNotify.success).toHaveBeenCalledWith('Webhook gerado com sucesso!');
    });
  });
});
