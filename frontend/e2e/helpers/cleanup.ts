import { type APIRequestContext } from '@playwright/test';

/**
 * Cleanup functions to reset the E2E user state in the real backend.
 * Fixed to work with direct backend access (port 8000).
 */
export async function cleanupUserData(api: APIRequestContext) {
  console.log('🧹 Cleaning up real E2E user data...');

  const endpoints = [
    { list: '/workout/list', key: 'workouts', del: '/workout/' },
    { list: '/nutrition/list', key: 'logs', del: '/nutrition/' },
    { list: '/weight', key: 'logs', del: '/weight/' },
    { list: '/memory/list', key: 'memories', del: '/memory/' }
  ];

  for (const ep of endpoints) {
    try {
      const res = await api.get(ep.list);
      if (res.ok()) {
        const data = await res.json();
        const items = data[ep.key] || [];
        for (const item of items) {
          const id = ep.key === 'logs' && ep.list.includes('weight') ? item.date.split('T')[0] : item.id;
          await api.delete(`${ep.del}${id}`);
        }
      }
    } catch (e) {
      // ignore
    }
  }

  // Reset Hevy Integration
  try {
    await api.post('/integrations/hevy/config', {
      data: { api_key: "", enabled: false }
    });
  } catch (e) { /* ignore */ }

  // Reset Telegram Integration
  try {
    await api.post('/telegram/unlink');
  } catch (e) { /* ignore */ }

  // Reset Profile to stable QA values
  try {
    await api.post('/user/update_profile', {
      data: {
        gender: 'Masculino',
        age: 30,
        weight: 80,
        height: 180,
        goal_type: 'maintain',
        weekly_rate: 0.5,
        onboarding_completed: true
      }
    });
  } catch (e) { /* ignore */ }

  console.log('✅ Cleanup complete.');
}

/**
 * Specifically resets the user to a state where onboarding is required.
 */
export async function resetOnboarding(api: APIRequestContext) {
  console.log('🔄 Resetting onboarding status...');
  await api.post('/user/update_profile', {
    data: {
      gender: 'Masculino',
      age: 30,
      weight: 80,
      height: 180,
      goal_type: 'maintain',
      weekly_rate: 0.5,
      onboarding_completed: false
    }
  });
}
