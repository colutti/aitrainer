import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';

import { useDemoMode } from '../../../shared/hooks/useDemoMode';
import { useNotificationStore } from '../../../shared/hooks/useNotification';
import { type UserProfile } from '../../../shared/types/user-profile';
import { settingsApi } from '../api/settings-api';
import { type UserProfileForm } from '../schemas/user-profile-schema';

import UserProfileView from './UserProfileView';

/**
 * UserProfilePage (Container)
 * 
 * Manages user profile data fetching and updates.
 */
const UserProfilePage = () => {
  const { t } = useTranslation();
  const notify = useNotificationStore();
  const { isReadOnly: isDemoUser } = useDemoMode();
  
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [photoBase64, setPhotoBase64] = useState<string | null>(null);

  const loadUserProfile = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await settingsApi.getProfile();
      setProfile(data);
    } catch {
      notify.error(t('settings.profile.load_error'));
    } finally {
      setIsLoading(false);
    }
  }, [notify, t]);

  useEffect(() => {
    void loadUserProfile();
  }, [loadUserProfile]);

  const handleSubmit = async (formData: UserProfileForm) => {
    if (isDemoUser) return;
    setIsSaving(true);
    try {
      // 1. Update Profile Stats (age, gender, goals, etc.)
      await settingsApi.updateProfile(formData);
      
      // 2. Update Identity (display_name) if changed
      if (formData.display_name && formData.display_name !== profile?.display_name) {
        await settingsApi.updateIdentity({ display_name: formData.display_name });
      }

      notify.success(t('settings.profile.save_success'));
      await loadUserProfile();
    } catch {
      notify.error(t('settings.profile.save_error'));
    } finally {
      setIsSaving(false);
    }
  };

  const handlePhotoUpload = async (file: File) => {
    if (isDemoUser) {
      return Promise.resolve();
    }
    return new Promise<void>((resolve) => {
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64 = reader.result as string;
        setIsSaving(true);
        try {
          await settingsApi.updateIdentity({ photo_base64: base64 });
          setPhotoBase64(base64);
          notify.success(t('settings.profile.photo_success'));
          await loadUserProfile();
        } catch {
          notify.error(t('settings.profile.photo_error'));
        } finally {
          setIsSaving(false);
          resolve();
        }
      };
      reader.readAsDataURL(file);
    });
  };

  return (
    <UserProfileView 
      profile={profile}
      isLoading={isLoading}
      isSaving={isSaving}
      photoBase64={photoBase64}
      isReadOnly={isDemoUser}
      onSubmit={handleSubmit}
      onPhotoUpload={handlePhotoUpload}
    />
  );
};

export default UserProfilePage;
