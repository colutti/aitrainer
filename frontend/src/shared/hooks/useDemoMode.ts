import { useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';

import { useAuthStore } from './useAuth';
import type { UserInfo } from './useAuth';
import { useNotificationStore } from './useNotification';

const DEFAULT_READ_ONLY_MESSAGE = 'Demo Read-Only';

export interface DemoModeGuard {
  isDemoUser: boolean;
  isReadOnly: boolean;
  readOnlyMessage: string;
  notifyReadOnly: () => void;
  blockIfReadOnly: (action?: () => void) => boolean;
}

type DemoModeSource = boolean | Pick<UserInfo, 'is_demo'> | null | undefined;

export function useDemoMode(overrideIsDemoUser?: DemoModeSource): DemoModeGuard {
  const { userInfo } = useAuthStore();
  const notify = useNotificationStore();
  const { t } = useTranslation();

  const isDemoUser =
    typeof overrideIsDemoUser === 'boolean'
      ? overrideIsDemoUser
      : overrideIsDemoUser?.is_demo === true || userInfo?.is_demo === true;
  const readOnlyMessage = useMemo(
    () => t('shared.read_only', DEFAULT_READ_ONLY_MESSAGE),
    [t]
  );

  const notifyReadOnly = useCallback(() => {
    notify.info(readOnlyMessage);
  }, [notify, readOnlyMessage]);

  const blockIfReadOnly = useCallback(
    (action?: () => void) => {
      if (isDemoUser) {
        notifyReadOnly();
        return true;
      }

      action?.();
      return false;
    },
    [isDemoUser, notifyReadOnly]
  );

  return {
    isDemoUser,
    isReadOnly: isDemoUser,
    readOnlyMessage,
    notifyReadOnly,
    blockIfReadOnly,
  };
}
