import { httpClient } from '../api/http-client';
import type { NutritionLog } from '../types/nutrition';

import { useNutritionStore } from './useNutrition';

// Mock httpClient
vi.mock('../api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('useNutritionStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useNutritionStore.getState().reset();
  });

  it('should have initial state', () => {
    const state = useNutritionStore.getState();
    expect(state.logs).toEqual([]);
    expect(state.stats).toBeNull();
    expect(state.isLoading).toBe(false);
  });

  it('should fetch stats successfully', async () => {
    const mockStats = {
      avg_daily_calories: 2000,
      total_logs: 10,
      today: null,
      weekly_adherence: [true, false],
    };

    vi.mocked(httpClient).mockResolvedValue(mockStats);

    await useNutritionStore.getState().fetchStats();

    const state = useNutritionStore.getState();
    expect(state.stats).toEqual(mockStats);
    expect(state.isLoading).toBe(false);
    expect(httpClient).toHaveBeenCalledWith('/nutrition/stats');
  });

  it('should handle delete log', async () => {
    const initialLogs: NutritionLog[] = [
      { id: '1', calories: 2000 } as unknown as NutritionLog,
      { id: '2', calories: 1800 } as unknown as NutritionLog,
    ];
    
    useNutritionStore.setState({ logs: initialLogs, total: 2 });
    vi.mocked(httpClient).mockResolvedValue({ message: 'Deleted' });

    await useNutritionStore.getState().deleteLog('1');

    const state = useNutritionStore.getState();
    expect(state.logs).toHaveLength(1);
    expect(state.logs[0].id).toBe('2');
    expect(httpClient).toHaveBeenCalledWith('/nutrition/1', { method: 'DELETE' });
  });
});
