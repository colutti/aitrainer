import { test, expect } from './fixtures';
import { bootstrapOnboardedUser } from './helpers/bootstrap';
import { t } from './helpers/translations';

test.describe('Dashboard Regressions', () => {
  test('keeps workout activity reachable after a hard reload and page scroll', async ({ authenticatedPage, ui }) => {
    await ui.navigateTo('workouts');
    await ui.openDrawer('Registrar Treino');

    const workoutType = `Dashboard Regression ${Date.now()}`;
    await ui.fillForm({
      [t('workouts.workout_type')]: workoutType,
      [t('workouts.duration')]: 35,
    });

    await authenticatedPage.getByRole('button', { name: /Adicionar/i }).click();
    await authenticatedPage.getByPlaceholder('Nome do Exercício').first().fill('Agachamento Livre');
    await ui.submit();

    await expect(authenticatedPage.getByTestId('workout-card').filter({ hasText: workoutType }).first()).toBeVisible({ timeout: 15000 });

    await ui.navigateTo('dashboard');
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('widget-metabolism')).toBeVisible({ timeout: 15000 });

    const footerNote = authenticatedPage.getByText(t('body.metabolism.info_desc'));
    await footerNote.scrollIntoViewIfNeeded();
    await expect(footerNote).toBeVisible({ timeout: 15000 });

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('widget-metabolism')).toBeVisible({ timeout: 15000 });
    await footerNote.scrollIntoViewIfNeeded();
    await expect(footerNote).toBeVisible({ timeout: 15000 });
  });

  test('keeps plan discovery handoff and persisted plan view coherent after reload', async ({ page, playwright }, testInfo) => {
    const authenticatedPage = await bootstrapOnboardedUser(page, testInfo);
    const token = await authenticatedPage.evaluate(() => localStorage.getItem('auth_token') ?? '');
    const api = await playwright.request.newContext({
      baseURL: process.env.E2E_API_BASE_URL ?? 'http://localhost:8000',
      extraHTTPHeaders: {
        Authorization: token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
      },
    });

    const discoveryResponse = await api.post('/plan/discovery', {
      data: {
        goal_primary: 'muscle_gain',
        goal_summary: 'Ganhar massa com menos gordura',
        target_date: '2026-08-01',
        training_days_available: ['monday', 'thursday'],
        session_duration_min: 60,
        constraints: ['nenhuma'],
        preferences: ['academia'],
        available_equipment: ['barra'],
        metabolism_confirmed: true,
      },
    });
    expect(discoveryResponse.ok()).toBeTruthy();

    await authenticatedPage.goto('/dashboard/plan', { waitUntil: 'networkidle' });
    await expect(authenticatedPage.getByTestId('plan-discovery-view')).toBeVisible({ timeout: 15000 });

    await authenticatedPage.getByRole('button', { name: t('plan.empty.cta') }).click();
    await expect(authenticatedPage).toHaveURL(/\/dashboard\/chat$/, { timeout: 15000 });
    await expect(authenticatedPage.getByTestId('chat-input')).toHaveValue(/Crie meu plano mestre de treino e nutrição\.|Discovery completo\. O proximo passo e criar o plano\./);

    const createPlanResponse = await api.post('/plan/create-from-discovery', {
      data: {
        title: 'Plano Mestre',
        goal: {
          primary_goal: 'muscle_gain',
          outcome_summary: 'Ganhar massa com superavit controlado',
          success_metrics: [
            {
              metric_name: 'peso',
              target_value: 75,
              unit: 'kg',
              direction: 'increase',
              deadline: '2026-08-01',
            },
          ],
        },
        timeline: {
          start_date: '2026-05-01',
          target_date: '2026-08-01',
          review_cadence_days: 7,
          current_phase: 'acumulacao',
        },
        user_context: {
          training_days_available: ['monday', 'thursday'],
          session_duration_min: 60,
          constraints: ['nenhuma'],
          preferences: ['academia'],
          available_equipment: ['barra'],
        },
        training: {
          split_name: 'upper_lower',
          frequency_per_week: 2,
          session_duration_min: 60,
          routines: [
            {
              id: 'upper_a',
              name: 'Upper A',
              exercises: [
                {
                  name: 'Supino Reto',
                  sets: 4,
                  rep_range: { min_reps: 6, max_reps: 8 },
                  intensity: {
                    prescription_type: 'rpe',
                    target: '8',
                  },
                  progression_rule: {
                    method: 'double_progression',
                    increase_when: 'bater topo da faixa',
                    hold_when: 'ficar no meio da faixa',
                    deload_when: 'regredir por 2 semanas',
                  },
                },
              ],
            },
            {
              id: 'lower_a',
              name: 'Lower A',
              exercises: [
                {
                  name: 'Agachamento',
                  sets: 4,
                  rep_range: { min_reps: 5, max_reps: 8 },
                  intensity: {
                    prescription_type: 'rpe',
                    target: '8',
                  },
                  progression_rule: {
                    method: 'linear_load',
                    increase_when: 'completar volume com tecnica boa',
                    hold_when: 'tecnica instavel',
                    deload_when: 'fadiga acumulada por 2 semanas',
                  },
                },
              ],
            },
          ],
          weekly_schedule: [
            { day: 'monday', routine_id: 'upper_a', focus: 'upper', type: 'training' },
            { day: 'thursday', routine_id: 'lower_a', focus: 'lower', type: 'training' },
          ],
        },
        nutrition: {
          daily_targets: {
            calories_kcal: 2600,
            protein_g: 160,
            carbs_g: 315,
            fat_g: 75,
          },
          strategy: 'superavit leve',
          adherence_target_pct: 85,
        },
        alignment: {
          training_nutrition_rationale: 'Superavit leve para hipertrofia.',
          energy_strategy: 'surplus',
          recovery_assumptions: ['dormir 7h'],
          conflict_rules: [
            {
              trigger: 'queda de performance',
              action: 'revisar recuperacao',
            },
          ],
        },
        tracking: {
          workout_adherence_target_pct: 85,
          nutrition_adherence_target_pct: 80,
          progress_markers: [
            {
              name: 'carga no supino',
              source: 'workouts',
              target_summary: 'subir carga ou reps',
            },
          ],
          review_questions: ['A recuperacao esta coerente?'],
        },
      },
    });
    expect(createPlanResponse.ok()).toBeTruthy();

    await authenticatedPage.goto('/dashboard/plan', { waitUntil: 'networkidle' });
    await expect(authenticatedPage.getByTestId('plan-view')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText('Plano Mestre')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText('Ganhar massa com superavit controlado')).toBeVisible({ timeout: 15000 });

    const weeklySchedule = authenticatedPage.getByTestId('plan-weekly-schedule');
    await expect(weeklySchedule.getByRole('button', { name: 'Segunda' })).toBeVisible();
    await expect(weeklySchedule.getByRole('button', { name: 'Quinta' })).toBeVisible();

    await weeklySchedule.getByRole('button', { name: 'Quinta' }).click();
    await expect(authenticatedPage.getByTestId('plan-daily-routine')).toContainText('Lower A');
    await expect(authenticatedPage.getByTestId('plan-weekly-exercises')).toContainText('Agachamento');

    const reviewResponse = await api.post('/plan/review', {
      data: {
        summary: 'Aderencia consistente na ultima semana',
        decision: 'manter estrategia atual',
        changes_made: ['Sem ajustes estruturais neste checkpoint.'],
        next_review_at: '2026-06-01',
        evidence_summary: ['Treinos presentes', 'Sem conflitos relevantes'],
      },
    });
    expect(reviewResponse.ok()).toBeTruthy();

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await expect(authenticatedPage.getByTestId('plan-view')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText('Aderencia consistente na ultima semana')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText('01/06/2026')).toBeVisible({ timeout: 15000 });

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await expect(authenticatedPage.getByTestId('plan-view')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText('Plano Mestre')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText('Aderencia consistente na ultima semana')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText('01/06/2026')).toBeVisible({ timeout: 15000 });
    await expect(weeklySchedule.getByRole('button', { name: 'Quinta' })).toBeVisible();
    await weeklySchedule.getByRole('button', { name: 'Quinta' }).click();
    await expect(authenticatedPage.getByTestId('plan-daily-routine')).toContainText('Lower A');
    await expect(authenticatedPage.getByTestId('plan-weekly-exercises')).toContainText('Agachamento');

    await api.dispose();
  });
});
