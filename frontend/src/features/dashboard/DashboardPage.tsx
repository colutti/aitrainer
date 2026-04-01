import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';

import { useAuthStore } from '../../shared/hooks/useAuth';
import { useDashboardStore } from '../../shared/hooks/useDashboard';
import { useNotificationStore } from '../../shared/hooks/useNotification';

import { DashboardView } from './components/DashboardView';

/**
 * DashboardPage component (Container)
 * 
 * Responsável por conectar com a API (via Zustand/React Query),
 * formatar os dados e passá-los para a View burra.
 */
export default function DashboardPage() {
  const { data, isLoading, fetchData } = useDashboardStore();
  const { loadUserInfo } = useAuthStore();
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const notification = useNotificationStore();
  const hasTriggeredPaymentToast = useRef(false);

  // Busca dados na montagem
  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  // Lógica de toast de pagamento do Stripe
  useEffect(() => {
    const paymentStatus = searchParams.get('payment');
    if (paymentStatus === 'success' && !hasTriggeredPaymentToast.current) {
      hasTriggeredPaymentToast.current = true;
      const handlePaymentSuccess = async () => {
        try {
          const updatedUser = await loadUserInfo();
          const updatedPlan = (updatedUser.subscription_plan ?? 'Free').toLowerCase().trim();
          if (updatedPlan !== 'free') {
            notification.success(
              t('landing.subscription.payment_success_message', {
                defaultValue: 'Pagamento realizado com sucesso! Bem-vindo ao time FityQ.',
              })
            );
          } else {
            notification.info(
              t('landing.subscription.payment_pending_message', {
                defaultValue: 'Pagamento recebido, mas o plano ainda está pendente de confirmação. Tente atualizar em instantes.',
              })
            );
          }
        } catch {
          notification.info(
            t('landing.subscription.payment_pending_message', {
              defaultValue: 'Pagamento recebido, mas o plano ainda está pendente de confirmação. Tente atualizar em instantes.',
            })
          );
        } finally {
          const newParams = new URLSearchParams(searchParams);
          newParams.delete('payment');
          setSearchParams(newParams, { replace: true });
        }
      };
      void handlePaymentSuccess();
    } else if (paymentStatus === 'cancelled' && !hasTriggeredPaymentToast.current) {
      hasTriggeredPaymentToast.current = true;
      notification.info(t('landing.subscription.payment_cancelled_message', { defaultValue: 'O processo de pagamento foi interrompido. Você pode tentar novamente quando quiser.' }));
      
      const newParams = new URLSearchParams(searchParams);
      newParams.delete('payment');
      setSearchParams(newParams, { replace: true });
    }
  }, [searchParams, setSearchParams, notification, t, loadUserInfo]);

  // Se os dados base não vieram da API ainda, garantimos um default
  const stats = data?.stats ?? {
    metabolism: {
      tdee: 0,
      daily_target: 0,
      confidence: 'none' as const,
      weekly_change: 0,
      energy_balance: 0,
      status: 'maintenance',
      macro_targets: null,
      goal_type: 'maintain' as const,
      consistency_score: 0,
      stability_score: 0
    },
    body: {
      weight_current: 0,
      weight_diff: 0,
      weight_diff_15: null,
      weight_diff_30: null,
      weight_trend: 'stable' as const,
      body_fat_pct: null,
      fat_diff: null,
      fat_diff_15: null,
      fat_diff_30: null,
      muscle_mass_pct: null,
      muscle_mass_kg: null,
      muscle_diff: null,
      muscle_diff_15: null,
      muscle_diff_30: null,
      muscle_diff_kg: null,
      muscle_diff_kg_15: null,
      muscle_diff_kg_30: null,
      bmr: null
    },
    calories: { consumed: 0, target: 0, percent: 0 },
    workouts: { completed: 0, target: 0 },
  };

  const { metabolism, body, calories, workouts } = stats;
  const { streak, weightHistory, recentPRs, strengthRadar, volumeTrend, weeklyFrequency } = data ?? {};

  // ==============================
  // Helpers de Formatação de Dados
  // ==============================

  const getMergedWeightData = (): { date: string; weight?: number; trend?: number }[] | null => {
    if (!data?.weightTrend || !weightHistory) return null;
    const dateMap = new Map<string, { date: string; weight?: number; trend?: number }>();

    weightHistory.forEach(point => {
      const dateStr = typeof point.date === 'string' ? point.date : String(point.date);
      const dateKey = dateStr.split('T')[0];
      if (dateKey) dateMap.set(dateKey, { date: dateKey, weight: point.weight });
    });

    data.weightTrend.forEach(point => {
      const dateStr = typeof point.date === 'string' ? point.date : String(point.date);
      const dateKey = dateStr.split('T')[0];
      if (dateKey) {
        const existing = dateMap.get(dateKey) ?? { date: dateKey };
        existing.trend = point.value; 
        dateMap.set(dateKey, existing);
      }
    });

    return Array.from(dateMap.values()).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  };

  const getMergedFatData = (): { date: string; value?: number; trend?: number }[] | null => {
    if (!data?.fatTrend) return null;
    const dateMap = new Map<string, { date: string; value?: number; trend?: number }>();

    if (data.fatHistory) {
      data.fatHistory.forEach((point) => {
        const dateKey = (typeof point.date === 'string' ? point.date : String(point.date)).split('T')[0];
        if (dateKey && typeof point.value === 'number') dateMap.set(dateKey, { date: dateKey, value: point.value });
      });
    }

    data.fatTrend.forEach((point) => {
      const dateKey = (typeof point.date === 'string' ? point.date : String(point.date)).split('T')[0];
      if (dateKey && typeof point.value === 'number') {
        const existing = dateMap.get(dateKey) ?? { date: dateKey };
        existing.trend = point.value;
        dateMap.set(dateKey, existing);
      }
    });

    return Array.from(dateMap.values()).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  };

  const getMergedMuscleData = (): { date: string; value?: number; trend?: number }[] | null => {
    if (!data?.muscleTrend) return null;
    const dateMap = new Map<string, { date: string; value?: number; trend?: number }>();

    if (data.muscleHistory) {
      data.muscleHistory.forEach((point) => {
        const dateKey = (typeof point.date === 'string' ? point.date : String(point.date)).split('T')[0];
        if (dateKey && typeof point.value === 'number') dateMap.set(dateKey, { date: dateKey, value: point.value });
      });
    }

    data.muscleTrend.forEach((point) => {
      const dateKey = (typeof point.date === 'string' ? point.date : String(point.date)).split('T')[0];
      if (dateKey && typeof point.value === 'number') {
        const existing = dateMap.get(dateKey) ?? { date: dateKey };
        existing.trend = point.value;
        dateMap.set(dateKey, existing);
      }
    });

    return Array.from(dateMap.values()).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  };

  const confidenceColor = {
    'high': 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
    'medium': 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
    'low': 'text-orange-400 bg-orange-400/10 border-orange-400/20',
    'none': 'text-text-muted bg-white/5 border-white/10'
  }[metabolism.confidence] ?? 'text-text-muted';

  const confidenceLevel = (metabolism.confidence === 'none' || !metabolism.confidence)
    ? t('dashboard.confidence_level.none')
    : t(`dashboard.confidence_level.${metabolism.confidence.toLowerCase()}`, { defaultValue: t('dashboard.confidence_level.unknown') });

  // Injeção de Dados na View
  return (
    <DashboardView 
      isLoading={isLoading && !data}
      metabolism={metabolism}
      body={body}
      mergedWeightData={getMergedWeightData()}
      mergedFatData={getMergedFatData()}
      mergedMuscleData={getMergedMuscleData()}
      recentActivities={data?.recentActivities ?? []}
      recentPRs={recentPRs ?? []}
      strengthRadar={strengthRadar ?? null}
      volumeTrend={volumeTrend ?? []}
      weeklyFrequency={weeklyFrequency ?? []}
      streak={streak ?? null}
      calories={calories}
      workouts={workouts}
      confidenceLevel={confidenceLevel}
      confidenceColor={confidenceColor}
    />
  );
  }
