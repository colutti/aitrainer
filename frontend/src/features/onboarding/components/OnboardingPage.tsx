import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams, useNavigate } from 'react-router-dom';

import { Button } from '../../../shared/components/ui/Button';
import { useAuthStore } from '../../../shared/hooks/useAuth';
import { useNotificationStore } from '../../../shared/hooks/useNotification';
import { usePublicConfig } from '../../../shared/hooks/usePublicConfig';
import { integrationsApi } from '../../settings/api/integrations-api';
import { onboardingApi, type OnboardingPayload } from '../api/onboarding-api';

import { OnboardingView } from './OnboardingView';

/**
 * OnboardingPage (Container)
 * 
 * Manages the onboarding wizard state and API calls.
 * Handles both invitation-based registration and public onboarding for existing users.
 */
export default function OnboardingPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { userInfo, loadUserInfo, isLoading: authLoading } = useAuthStore();
  const { enableNewUserSignups } = usePublicConfig();
  const notify = useNotificationStore();
  
  const token = searchParams.get('token');

  const [step, setStep] = useState(0); 
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState<Partial<OnboardingPayload>>({
    goal_type: 'maintain',
    weekly_rate: 0.5,
    trainer_type: 'gymbro',
    subscription_plan: 'Free'
  });
  
  const [email, setEmail] = useState('');
  const [hevyApiKey, setHevyApiKey] = useState('');
  const [connectingHevy, setConnectingHevy] = useState(false);
  const [importing, setImporting] = useState<string | null>(null);
  
  useEffect(() => {
    if (authLoading) return;

    async function validate() {
      // Flow 1: Already authenticated user without onboarding
      if (userInfo && !userInfo.onboarding_completed) {
        setStep(2);
        if (userInfo.name && !formData.name) {
          setFormData(prev => ({ ...prev, name: userInfo.name }));
        }
        return;
      }

      // Flow 2: Invitation Token
      if (!token) {
        // If not logged in and no token, redirect to landing
        if (!userInfo) {
          void navigate('/');
        }
        return;
      }
      
      try {
        const res = await onboardingApi.validateToken(token);
        if (res.valid && res.email) {
          setEmail(res.email);
          setStep(1); // Password step
        } else {
          setError(t('onboarding.tokens.invalid'));
        }
      } catch {
        setError(t('onboarding.tokens.validation_error'));
      }
    }
    void validate();
  }, [token, t, userInfo, formData.name, authLoading, navigate]);

  const handleNext = () => { setStep(s => s + 1); };
  const handleBack = () => { setStep(s => s - 1); };

  const handleSubmitProfile = async () => {
    setLoading(true);
    try {
      const payload = {
        gender: formData.gender ?? 'Masculino',
        age: Number(formData.age),
        weight: Number(formData.weight),
        height: Number(formData.height),
        goal_type: formData.goal_type ?? 'maintain',
        weekly_rate: Number(formData.weekly_rate),
        trainer_type: formData.trainer_type ?? 'gymbro',
        subscription_plan: formData.subscription_plan ?? 'Free',
        name: formData.name
      };

      if (userInfo && !userInfo.onboarding_completed) {
        // Public Flow
        const res = await onboardingApi.completePublicOnboarding(payload);
        localStorage.setItem('auth_token', res.token);
        
        // Handle Plan Redirect
        const planId = formData.subscription_plan?.toLowerCase();
        if (planId && planId !== 'free') {
          if (!enableNewUserSignups) {
            notify.info(t('settings.subscription.new_sales_disabled'));
            await loadUserInfo();
            setStep(5);
            return;
          }

          const { stripeApi } = await import('../../../shared/api/stripe-api');
          const { STRIPE_PRICE_IDS } = await import('../../../shared/constants/stripe');
          const priceId = STRIPE_PRICE_IDS[planId as keyof typeof STRIPE_PRICE_IDS];
          
          if (priceId) {
            const url = await stripeApi.createCheckoutSession(
              priceId,
              window.location.origin + '/dashboard?payment=success',
              window.location.origin + '/onboarding'
            );
            window.location.href = url;
            return;
          }
        }
        
        await loadUserInfo();
        setStep(5); // Go to integrations
      } else {
        // Invitation Flow (Simplified for public flow primary)
        setStep(5);
      }
    } catch (err) {
      console.error(err);
      notify.error(t('onboarding.errors.creation_error'));
    } finally {
      setLoading(false);
    }
  };

  const handleHevyConnect = async () => {
    if (!hevyApiKey) return;
    setConnectingHevy(true);
    try {
      await integrationsApi.saveHevyKey(hevyApiKey);
      notify.success(t('onboarding.hevy_connected_success'));
    } catch {
      notify.error(t('onboarding.hevy_error_connect'));
    } finally {
      setConnectingHevy(false);
    }
  };

  const handleUpload = async (file: File, type: 'mfp' | 'zepp') => {
    setImporting(type);
    try {
      const res = type === 'mfp' 
        ? await integrationsApi.uploadMfpCsv(file)
        : await integrationsApi.uploadZeppLifeCsv(file);
        
      notify.success(t('onboarding.import_success', { created: String(res.created) }));
    } catch {
      notify.error(t('onboarding.import_error'));
    } finally {
      setImporting(null);
    }
  };

  const handleFinish = () => {
    void navigate('/dashboard');
  };

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#09090b] text-white p-4">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-black uppercase text-red-500">{t('onboarding.error_title')}</h1>
          <p className="text-zinc-500">{error}</p>
          <Button onClick={() => { void navigate('/'); }}>{t('common.back')}</Button>
        </div>
      </div>
    );
  }

  return (
    <OnboardingView 
      step={step}
      onNext={handleNext}
      onBack={handleBack}
      onSubmit={handleSubmitProfile}
      onFinish={handleFinish}
      formData={formData}
      setFormData={setFormData}
      loading={loading}
      email={email}
      hevyApiKey={hevyApiKey}
      setHevyApiKey={setHevyApiKey}
      onHevyConnect={handleHevyConnect}
      connectingHevy={connectingHevy}
      onUpload={handleUpload}
      importing={importing}
    />
  );
}
