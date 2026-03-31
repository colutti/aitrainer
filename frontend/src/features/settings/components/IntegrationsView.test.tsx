import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { IntegrationsView } from './IntegrationsView';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: any) => {
      if (key === 'settings.integrations.shared.active' && options?.key) return `Active ${options.key}`;
      if (key === 'settings.integrations.telegram.connected' && options?.username) return `Connected to ${options.username}`;
      return key;
    },
  }),
}));

const mockProps = {
  hevy: {
    status: { enabled: true, hasKey: true, apiKeyMasked: '****1234', lastSync: '2024-01-01T10:00:00Z' },
    key: '',
    setKey: vi.fn(),
    onSave: vi.fn(),
    onSync: vi.fn(),
    onRemove: vi.fn(),
    loading: false,
    syncing: false,
  },
  webhook: {
    config: { hasWebhook: true, webhookUrl: 'http://test.com', authHeader: 'Bearer 123' },
    credentials: null,
    onGenerate: vi.fn(),
    onRevoke: vi.fn(),
    onCopy: vi.fn(),
    loading: false,
  },
  telegram: {
    status: { linked: true, telegram_username: 'test_user', telegram_notify_on_workout: true },
    code: null,
    onGenerate: vi.fn(),
    onToggleNotify: vi.fn(),
    loading: false,
    notifyOnWorkout: true,
  },
  imports: {
    onUpload: vi.fn(),
    importing: false,
  }
  ,
  isReadOnly: false
};

describe('IntegrationsView', () => {
  it('renders correctly when connected to Hevy', () => {
    render(<IntegrationsView {...mockProps} />);
    expect(screen.getByText(/Active \*\*\*\*1234/i)).toBeInTheDocument();
    expect(screen.getByText(/settings\.integrations\.hevy\.sync_button/i)).toBeInTheDocument();
  });

  it('renders telegram username when linked', () => {
    render(<IntegrationsView {...mockProps} />);
    expect(screen.getByText(/Connected to test_user/i)).toBeInTheDocument();
  });

  it('calls onSync when Hevy sync button clicked', () => {
    render(<IntegrationsView {...mockProps} />);
    const syncBtn = screen.getByText(/settings\.integrations\.hevy\.sync_button/i);
    fireEvent.click(syncBtn);
    expect(mockProps.hevy.onSync).toHaveBeenCalled();
  });

  it('calls onToggleNotify when telegram checkbox clicked', () => {
    render(<IntegrationsView {...mockProps} />);
    const checkbox = screen.getByRole('checkbox');
    fireEvent.click(checkbox);
    expect(mockProps.telegram.onToggleNotify).toHaveBeenCalled();
  });

  it('disables integration controls in read-only mode', () => {
    render(<IntegrationsView {...mockProps} isReadOnly />);
    expect(screen.getByText('Demo Read-Only')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'settings.integrations.hevy.sync_button' })).toBeDisabled();
    expect(screen.getByRole('checkbox')).toBeDisabled();
  });

  it('keeps imports section above previous cards', () => {
    render(<IntegrationsView {...mockProps} />);
    const heading = screen.getByText(/settings\.integrations\.imports\.title/i);
    const section = heading.closest('div');
    expect(section).toHaveClass('relative');
    expect(section).toHaveClass('z-10');
  });
});
