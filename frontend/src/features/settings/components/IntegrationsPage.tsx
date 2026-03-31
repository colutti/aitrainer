import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';

import { useDemoMode } from '../../../shared/hooks/useDemoMode';
import { useNotificationStore } from '../../../shared/hooks/useNotification';
import type { HevyStatus, ImportResult, TelegramStatus } from '../../../shared/types/integration';
import { integrationsApi } from '../api/integrations-api';

import { IntegrationsView } from './IntegrationsView';

/**
 * IntegrationsPage component (Container)
 * 
 * Manages external service connections (Hevy, Telegram) and data imports.
 * Delegates rendering to IntegrationsView.
 */
export default function IntegrationsPage() {
  const { t } = useTranslation();
  const notify = useNotificationStore();
  const { isReadOnly: isDemoUser } = useDemoMode();
  
  // Hevy State
  const [hevyStatus, setHevyStatus] = useState<HevyStatus | null>(null);
  const [hevyKey, setHevyKey] = useState('');
  const [hevyLoading, setHevyLoading] = useState(false);
  const [hevySyncing, setHevySyncing] = useState(false);

  // Telegram State
  const [telegramStatus, setTelegramStatus] = useState<TelegramStatus | null>(null);
  const [telegramCode, setTelegramCode] = useState<{ code: string; url: string } | null>(null);
  const [telegramLoading, setTelegramLoading] = useState(false);
  const [telegramNotifyOnWorkout, setTelegramNotifyOnWorkout] = useState(true);

  // Import State
  const [importing, setImporting] = useState(false);

  const loadHevyStatus = useCallback(async () => {
    try {
      const status = await integrationsApi.getHevyStatus();
      setHevyStatus(status ?? null);
    } catch { /* ignore */ }
  }, []);

  const loadTelegramStatus = useCallback(async () => {
    try {
      const status = await integrationsApi.getTelegramStatus();
      setTelegramStatus(status ?? null);
      if (status) {
        setTelegramNotifyOnWorkout(status.telegram_notify_on_workout ?? true);
      }
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    void loadHevyStatus();
    void loadTelegramStatus();
  }, [loadHevyStatus, loadTelegramStatus]);

  const handleSaveHevy = () => {
    if (isDemoUser) return;
    const run = async () => {
      if (!hevyKey) return;
      setHevyLoading(true);
      try {
        const status = await integrationsApi.saveHevyKey(hevyKey);
        setHevyStatus(status ?? null);
        setHevyKey('');
        notify.success(t('settings.integrations.hevy.save_success'));
      } catch {
        notify.error(t('settings.integrations.hevy.save_error'));
      } finally {
        setHevyLoading(false);
      }
    };
    void run();
  };

  const handleSyncHevy = () => {
    if (isDemoUser) return;
    const run = async () => {
      setHevySyncing(true);
      try {
        const res = await integrationsApi.syncHevy();
        if (res) {
          notify.success(t('settings.integrations.hevy.sync_success', { 
            imported: String(res.imported), 
            skipped: String(res.skipped) 
          }));
          await loadHevyStatus();
        }
      } catch {
        notify.error(t('settings.integrations.hevy.sync_error'));
      } finally {
        setHevySyncing(false);
      }
    };
    void run();
  };

  const handleRemoveHevy = () => {
    if (isDemoUser) return;
    const run = async () => {
      setHevyLoading(true);
      try {
        const status = await integrationsApi.removeHevyKey();
        setHevyStatus(status ?? null);
        notify.success(t('settings.integrations.hevy.remove_success'));
      } catch {
        notify.error(t('settings.integrations.hevy.remove_error'));
      } finally {
        setHevyLoading(false);
      }
    };
    void run();
  };

  const handleGenerateTelegram = () => {
    if (isDemoUser) return;
    const run = async () => {
      setTelegramLoading(true);
      try {
        const res = await integrationsApi.generateTelegramCode();
        setTelegramCode(res ?? null);
      } catch {
        notify.error(t('settings.integrations.telegram.generate_error'));
      } finally {
        setTelegramLoading(false);
      }
    };
    void run();
  };

  const handleTelegramNotificationChange = (value: boolean) => {
    if (isDemoUser) return;
    const run = async () => {
      try {
        await integrationsApi.updateTelegramNotifications({
          telegram_notify_on_workout: value
        });
        setTelegramNotifyOnWorkout(value);
        notify.success(t('settings.integrations.telegram.notification_update_success'));
      } catch {
        notify.error(t('settings.integrations.telegram.notification_update_error'));
      }
    };
    void run();
  };

  const handleUpload = (file: File, type: 'mfp' | 'zepp') => {
    if (isDemoUser) return;
    const run = async () => {
      setImporting(true);
      try {
        let res: ImportResult;
        if (type === 'mfp') {
          res = await integrationsApi.uploadMfpCsv(file);
        } else {
          res = await integrationsApi.uploadZeppLifeCsv(file);
        }
        
        notify.success(t('settings.integrations.imports.success', { 
          created: String(res.created), 
          updated: String(res.updated) 
        }));
        if (res.errors > 0) {
          notify.info(t('settings.integrations.imports.errors_found', { count: res.errors }));
        }
      } catch (err) {
        console.error(err);
        notify.error(t('settings.integrations.imports.error'));
      } finally {
        setImporting(false);
      }
    };
    void run();
  };

  return (
    <IntegrationsView 
      hevy={{
        status: hevyStatus,
        key: hevyKey,
        setKey: setHevyKey,
        onSave: handleSaveHevy,
        onSync: handleSyncHevy,
        onRemove: handleRemoveHevy,
        loading: hevyLoading,
        syncing: hevySyncing
      }}
      telegram={{
        status: telegramStatus,
        code: telegramCode,
        onGenerate: handleGenerateTelegram,
        onToggleNotify: handleTelegramNotificationChange,
        loading: telegramLoading,
        notifyOnWorkout: telegramNotifyOnWorkout
      }}
      imports={{
        onUpload: handleUpload,
        importing: importing
      }}
      isReadOnly={isDemoUser}
    />
  );
}
