import { ApiClient } from './api-client';

/**
 * Cleanup functions to reset the E2E user state
 */
export async function cleanupUserData(api: ApiClient) {
  console.log('🧹 Cleaning up E2E user data...');

  // 1. Workouts
  const workoutsRes = await api.get('/workout/list');
  if (workoutsRes.ok()) {
    const data = await workoutsRes.json();
    const workouts = data.workouts || []; // Fix: correctly access the array
    for (const w of workouts) {
      await api.delete(`/workout/${w.id}`);
    }
  }

  // 2. Nutrition
  const nutritionRes = await api.get('/nutrition/list');
  if (nutritionRes.ok()) {
    const data = await nutritionRes.json();
    const logs = data.logs || []; // Fix: correctly access the array
    for (const l of logs) {
      await api.delete(`/nutrition/${l.id}`);
    }
  }

  // 3. Weight
  // The weights endpoint returns a dict with 'logs'
  const weightRes = await api.get('/weight');
  if (weightRes.ok()) {
    const data = await weightRes.json();
    const logs = data.logs || [];
    for (const l of logs) {
      // WEIGHT DELETE uses date string (YYYY-MM-DD)
      const dateStr = l.date.split('T')[0];
      await api.delete(`/weight/${dateStr}`);
    }
  }

  // 4. Memories
  const memoriesRes = await api.get('/memory/');
  if (memoriesRes.ok()) {
    const data = await memoriesRes.json();
    const memories = data.memories || [];
    for (const m of memories) {
      await api.delete(`/memory/${m.id}`);
    }
  }

  // 5. Reset Profile to defaults
  await api.post('/user/update_profile', {
    gender: 'Masculino',
    age: 30,
    weight: 80,
    height: 180,
    goal_type: 'maintain',
    weekly_rate: 0.5,
    onboarding_completed: true
  });

  // 6. Reset Trainer to GymBro
  await api.post('/trainer/update_trainer_profile', {
    trainer_id: 'GymBro'
  });

  // 7. Reset Subscription (via simulated webhook)
  await api.post('/stripe/webhook', {
    type: 'customer.subscription.deleted',
    data: {
      object: {
        customer: 'cus_E2E_BOT_ID',
        metadata: {
          user_email: 'e2e-bot@fityq.it'
        }
      }
    }
  });

  console.log('✅ Cleanup complete.');
}
