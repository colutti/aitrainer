import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useNotificationStore } from '../../../shared/hooks/useNotification';
import { integrationsApi } from '../api/integrations-api';

import IntegrationsPage from './IntegrationsPage';

// Mocks
vi.mock('../api/integrations-api', () => ({
  integrationsApi: {
    getHevyStatus: vi.fn(),
    getTelegramStatus: vi.fn(),
    saveHevyKey: vi.fn(),
    removeHevyKey: vi.fn(),
    syncHevy: vi.fn(),
    generateTelegramCode: vi.fn(),
    updateTelegramNotifications: vi.fn(),
    uploadMfpCsv: vi.fn(),
    uploadZeppLifeCsv: vi.fn(),
  },
}));

vi.mock('../../../shared/hooks/useNotification', () => ({
  useNotificationStore: vi.fn(),
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: any) => {
      if (key === 'settings.integrations.shared.active' && options?.key) return `Active ${options.key}`;
      return key;
    },
  }),
}));

describe('IntegrationsPage', () => {
  const mockNotify = {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNotificationStore).mockReturnValue(mockNotify as any);
    vi.mocked(integrationsApi.getHevyStatus).mockResolvedValue({ hasKey: false } as any);
    vi.mocked(integrationsApi.getTelegramStatus).mockResolvedValue({ linked: false } as any);
  });

  it('should load initial statuses on mount', async () => {
    render(<IntegrationsPage />);
    await waitFor(() => {
      expect(integrationsApi.getHevyStatus).toHaveBeenCalled();
      expect(integrationsApi.getTelegramStatus).toHaveBeenCalled();
    });
  });

  it('should handle saving hevy key', async () => {
    vi.mocked(integrationsApi.saveHevyKey).mockResolvedValue({ hasKey: true, apiKeyMasked: '****5678' } as any);
    render(<IntegrationsPage />);
    
    const input = screen.getByPlaceholderText(/settings\.integrations\.hevy\.hevy_placeholder/i);
    fireEvent.change(input, { target: { value: 'my-new-key' } });
    
    const confirmBtn = screen.getByText(/common\.confirm/i);
    fireEvent.click(confirmBtn);
    
    await waitFor(() => {
      expect(integrationsApi.saveHevyKey).toHaveBeenCalledWith('my-new-key');
      expect(mockNotify.success).toHaveBeenCalled();
    });
  });

  it('should handle removing hevy key', async () => {
    vi.mocked(integrationsApi.getHevyStatus).mockResolvedValue({ hasKey: true, apiKeyMasked: '****1234' } as any);
    vi.mocked(integrationsApi.removeHevyKey).mockResolvedValue({ hasKey: false } as any);
    
    render(<IntegrationsPage />);
    
    await waitFor(() => screen.getByText(/Active \*\*\*\*1234/i));
    
    const removeBtn = screen.getByText(/settings\.integrations\.shared\.remove/i);
    fireEvent.click(removeBtn);
    
    await waitFor(() => {
      expect(integrationsApi.removeHevyKey).toHaveBeenCalled();
      expect(screen.getByPlaceholderText(/settings\.integrations\.hevy\.hevy_placeholder/i)).toBeInTheDocument();
    });
  });
});
