/**
 * VirtualBackend - A class that simulates the Backend API logic in-memory.
 * Used to power E2E tests without needing a running Backend container.
 */

interface VirtualResponse {
  status: number;
  body: any;
  contentType?: string;
}

export class VirtualBackend {
  private state = {
    user: {
      email: 'e2e-bot@fityq.it',
      name: 'E2E Bot',
      display_name: 'E2E Bot',
      role: 'user',
      onboarding_completed: true,
      subscription_plan: 'Free',
      gender: 'Masculino',
      age: 30,
      weight: 80,
      height: 180,
      goal_type: 'maintain',
      daily_msg_count: 5,
      daily_msg_limit: 10,
      effective_remaining_messages: 5,
      current_daily_limit: 10
    },
    workouts: [] as any[],
    nutrition: [] as any[],
    weights: [] as any[],
    memories: [] as any[],
    chat_history: [] as any[],
    trainers: [
      { trainer_id: 'atlas', name: 'Atlas', description: 'Focado em força', trainer_type: 'atlas' },
      { trainer_id: 'gymbro', name: 'Breno', description: 'Seu parceiro de treino', trainer_type: 'gymbro' }
    ],
    active_trainer: {
      trainer_id: 'gymbro',
      trainer_type: 'gymbro',
      name: 'Breno'
    }
  };

  public token = 'mock-v-token';

  setUser(user: any) {
    this.state.user = { ...this.state.user, ...user };
    if (user.subscription_plan === 'Pro') {
        this.state.user.effective_remaining_messages = 100;
        this.state.user.current_daily_limit = 100;
    }
  }

  /**
   * Internal dispatcher to handle different routes
   */
  async handleRequest(method: string, url: string, body?: any): Promise<VirtualResponse> {
    const rawUrl = new URL(url, 'http://localhost:8000');
    const rawPath = rawUrl.pathname;
    // Normalize path: remove /api and trailing slashes
    let path = rawPath.startsWith('/api') ? rawPath.replace('/api', '') : rawPath;
    if (path.length > 1 && path.endsWith('/')) {
        path = path.slice(0, -1);
    }

    const response: VirtualResponse = { status: 200, body: {} };

    // User Profile
    if (path === '/user/me' || path === '/user/profile') {
      response.body = this.state.user;
    }
    else if (path === '/user/update_profile' && method === 'POST') {
      this.state.user = { ...this.state.user, ...body };
      response.body = { message: 'Profile updated' };
    }
    else if (path === '/user/update_identity' && method === 'POST') {
      this.state.user = { ...this.state.user, ...body };
      response.body = { message: 'Identity updated' };
    }
    // Workouts
    else if (path === '/workout/list' || path === '/workout') {
      if (method === 'GET') {
        response.body = { 
          workouts: this.state.workouts || [], 
          total: this.state.workouts.length,
          page: 1, page_size: 10, total_pages: 1
        };
      } else if (method === 'POST') {
        const id = `w_${Date.now().toString()}`;
        const newWorkout = { 
          id, 
          date: body?.date || new Date().toISOString(), 
          workout_type: body?.workout_type || 'Geral',
          exercises: body?.exercises || [],
          duration_minutes: Number(body?.duration_minutes) || 45,
          source: 'manual',
          external_id: null,
          notes: body?.notes || ''
        };
        this.state.workouts.push(newWorkout);
        response.body = { id };
      }
    }
    else if (path === '/workout/stats') {
        response.body = { completed: this.state.workouts.length, target: 4 };
    }
    else if (path.startsWith('/workout/') && method === 'DELETE') {
      const id = path.split('/').pop();
      this.state.workouts = this.state.workouts.filter(w => w.id !== id);
      response.body = { message: 'Deleted' };
    }
    // Nutrition
    else if (path === '/nutrition/list') {
      response.body = { logs: this.state.nutrition || [] };
    }
    else if (path === '/nutrition/stats') {
        const consumed = this.state.nutrition.reduce((acc, n) => acc + (Number(n.calories) || 0), 0);
        response.body = { consumed, target: 2500, percent: Math.round((consumed / 2500) * 100) };
    }
    else if (path === '/nutrition/log' && method === 'POST') {
      const id = `n_${Date.now().toString()}`;
      const log = { 
        id, 
        date: body?.date || new Date().toISOString(), 
        calories: Number(body?.calories) || 0,
        protein_grams: Number(body?.protein_grams) || 0,
        carbs_grams: Number(body?.carbs_grams) || 0,
        fat_grams: Number(body?.fat_grams) || 0,
        fiber_grams: Number(body?.fiber_grams) || 0,
        source: body?.source || 'manual'
      };
      this.state.nutrition.push(log);
      response.body = { id };
    }
    else if (path.startsWith('/nutrition/') && method === 'DELETE') {
      const id = path.split('/').pop();
      this.state.nutrition = this.state.nutrition.filter(l => l.id !== id);
      response.body = { message: 'Deleted' };
    }
    // Metabolism
    else if (path === '/metabolism/stats') {
        response.body = {
            tdee: 2436,
            daily_target: 2436,
            confidence: 'medium',
            weight_change_per_week: -0.2,
            goal_type: this.state.user.goal_type,
            energy_balance: -100,
            macro_targets: { protein: 126, fat: 68, carbs: 280 },
            consistency_score: 85,
            stability_score: 90
        };
    }
    // Weight
    else if (path === '/weight') {
      if (method === 'GET' || (method === 'POST' && !body)) {
        response.body = { logs: this.state.weights || [] };
      } else if (method === 'POST') {
        const date = body?.date || new Date().toISOString().split('T')[0];
        const log = { 
            date, 
            weight_kg: Number(body?.weight_kg) || 0,
            trend_weight: Number(body?.weight_kg),
            body_fat_pct: body?.body_fat_pct ? Number(body.body_fat_pct) : 18,
            muscle_mass_pct: body?.muscle_mass_pct ? Number(body.muscle_mass_pct) : 40,
            muscle_mass_kg: body?.muscle_mass_kg ? Number(body.muscle_mass_kg) : 40
        };
        this.state.weights = this.state.weights.filter(w => w.date !== date);
        this.state.weights.push(log);
        response.body = { success: true };
      }
    }
    else if (path === '/weight/stats') {
        response.body = { weight_current: this.state.weights[this.state.weights.length - 1]?.weight_kg || 80, weight_trend: 'stable' };
    }
    else if (path.startsWith('/weight/') && method === 'DELETE') {
      const date = path.split('/').pop();
      this.state.weights = this.state.weights.filter(w => w.date !== date);
      response.body = { success: true };
    }
    // Trainer
    else if (path === '/trainer/trainer_profile') {
      response.body = this.state.active_trainer;
    }
    else if (path === '/trainer/available_trainers') {
      response.body = this.state.trainers;
    }
    else if (path === '/trainer/update_trainer_profile' && method === 'POST') {
      const tid = body?.trainer_id?.toLowerCase();
      const trainer = this.state.trainers.find(t => t.trainer_id === tid) || this.state.trainers[1];
      if (trainer) {
        this.state.active_trainer = { 
          trainer_id: trainer.trainer_id,
          trainer_type: trainer.trainer_type,
          name: trainer.name
        };
      }
      response.body = { message: 'Trainer updated' };
    }
    // Chat
    else if (path === '/message/history') {
      return { status: 200, body: this.state.chat_history || [] };
    }
    else if (path === '/message' && method === 'POST') {
      if (body?.message && !body?.user_message) {
          const userMsg = { sender: 'Student', text: body.message, timestamp: new Date().toISOString() };
          this.state.chat_history.push(userMsg);
          response.body = { success: true };
      } else {
          const text = "Eu sou seu treinador virtual.";
          return { status: 200, body: text, contentType: 'text/plain' };
      }
    }
    // Memories
    else if (path === '/memory/list' || path === '/memory') {
      if (method === 'GET') {
        response.body = { 
          memories: this.state.memories || [],
          total: this.state.memories.length,
          page: 1, page_size: 20, total_pages: 1
        };
      } else {
        const id = `m_${Date.now().toString()}`;
        this.state.memories.push({ id, memory: body?.memory || body?.content, created_at: new Date().toISOString() });
        response.body = { id };
      }
    }
    else if (path.startsWith('/memory/') && method === 'DELETE') {
      const id = path.split('/').pop();
      this.state.memories = this.state.memories.filter(m => m.id !== id);
      response.body = { success: true };
    }
    // Onboarding
    else if (path === '/onboarding/profile' && method === 'POST') {
      this.state.user.onboarding_completed = true;
      if (body?.name) this.state.user.name = body.name;
      response.body = { token: 'new-token', message: 'Success' };
    }
    // Dashboard
    else if (path === '/dashboard') {
      const recentActivities = [
        ...this.state.workouts.map(w => ({ id: w.id, type: 'workout', title: 'Treino', subtitle: w.workout_type || 'Manual', date: w.date })),
        ...this.state.nutrition.map(n => ({ id: n.id, type: 'nutrition', title: 'Refeição', subtitle: `${n.calories.toString()} kcal`, date: n.date })),
        ...this.state.weights.map(w => ({ id: `wt_${w.date as string}`, type: 'weight', title: 'Pesagem', subtitle: `${w.weight_kg.toString()} kg`, date: w.date }))
      ].sort((a, b) => new Date(b.date as string).getTime() - new Date(a.date as string).getTime());

      response.body = {
        streak: { current_weeks: 1, current_days: 3 },
        stats: {
          metabolism: { 
            tdee: 2436, daily_target: 2436, confidence: 'medium', weekly_change: -0.2, 
            goal_type: this.state.user.goal_type, status: 'maintenance', daily_target_calories: 2436,
            consistency_score: 85, energy_balance: 0, 
            macro_targets: { protein: 126, fat: 68, carbs: 280 }
          },
          body: { 
            weight_current: this.state.weights[this.state.weights.length - 1]?.weight_kg || 80, 
            weight_trend: 'stable', weight_diff: 0, weight_diff_15: 0, weight_diff_30: 0,
            body_fat_pct: this.state.weights[this.state.weights.length - 1]?.body_fat_pct || 18,
            muscle_mass_kg: this.state.weights[this.state.weights.length - 1]?.muscle_mass_kg || 40,
            muscle_mass_pct: this.state.weights[this.state.weights.length - 1]?.muscle_mass_pct || 40,
            fat_diff: 0, fat_diff_15: 0, fat_diff_30: 0,
            muscle_diff_kg: 0, muscle_diff_kg_15: 0, muscle_diff_kg_30: 0
          },
          calories: { consumed: this.state.nutrition.reduce((acc, n) => acc + (Number(n.calories) || 0), 0), target: 2436, percent: 0 },
          workouts: { completed: this.state.workouts.length, target: 4 }
        },
        weightHistory: this.state.weights.map(w => ({ date: w.date, value: w.weight_kg })),
        weightTrend: this.state.weights.map(w => ({ date: w.date, value: w.weight_kg })),
        fatHistory: this.state.weights.map(w => ({ date: w.date, value: w.body_fat_pct || 18 })),
        fatTrend: this.state.weights.map(w => ({ date: w.date, value: w.body_fat_pct || 18 })),
        muscleHistory: this.state.weights.map(w => ({ date: w.date, value: w.muscle_mass_kg || 40 })),
        muscleTrend: this.state.weights.map(w => ({ date: w.date, value: w.muscle_mass_kg || 40 })),
        recentPRs: [],
        strengthRadar: { push: 0.5, pull: 0.5, legs: 0.5, core: 0.5 },
        volumeTrend: [],
        weeklyFrequency: [false, true, false, true, false, false, false],
        recentActivities: recentActivities || []
      };
    }
    // Telegram
    else if (path === '/telegram/status') {
        response.body = { linked: false };
    }
    else if (path === '/telegram/generate-code' && method === 'POST') {
        response.body = { code: '123456', url: 'https://t.me/mock_bot' };
    }
    // Integrations
    else if (path === '/integrations/hevy/status') {
      response.body = { connected: false };
    }
    else if (path === '/integrations/hevy/webhook/config') {
        response.body = { hasWebhook: false };
    }
    else if (path === '/integrations/hevy/config' && method === 'POST') {
        response.body = { status: 'success' };
    }
    else if (path === '/integrations/zepp_life/import' && method === 'POST') {
        response.body = { created: 1, updated: 0, errors: 0 };
    }
    else if (path === '/integrations/mfp/import' && method === 'POST') {
        response.body = { created: 1, updated: 0, errors: 0 };
    }
    // Stripe
    else if (path === '/stripe/webhook' && method === 'POST') {
      const type = body?.type;
      const plan = body?.data?.object?.metadata?.plan;
      if (type === 'customer.subscription.created' || type === 'checkout.session.completed') {
        this.setUser({ subscription_plan: plan || 'Basic' });
      }
      if (type === 'customer.subscription.deleted') {
        this.setUser({ subscription_plan: 'Free' });
      }
      response.body = { received: true };
    }
    else {
      response.body = { status: 'ok', mocked: true };
    }

    return response;
  }

  // --- ApiClient Interface Compatibility ---

  private wrapResponse(status: number, body: any, contentType = 'application/json') {
    return {
      status: () => status,
      ok: () => status >= 200 && status < 300,
      json: async () => body,
      text: async () => typeof body === 'string' ? body : JSON.stringify(body),
      contentType: () => contentType
    };
  }

  async get(endpoint: string) {
    const res = await this.handleRequest('GET', endpoint);
    return this.wrapResponse(res.status, res.body, res.contentType);
  }

  async post(endpoint: string, data: any) {
    const res = await this.handleRequest('POST', endpoint, data);
    return this.wrapResponse(res.status, res.body, res.contentType);
  }

  async put(endpoint: string, data: any) {
    const res = await this.handleRequest('PUT', endpoint, data);
    return this.wrapResponse(res.status, res.body, res.contentType);
  }

  async delete(endpoint: string) {
    const res = await this.handleRequest('DELETE', endpoint);
    return this.wrapResponse(res.status, res.body, res.contentType);
  }
}
