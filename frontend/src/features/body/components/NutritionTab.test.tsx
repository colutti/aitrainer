import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useNutritionStore } from '../../../shared/hooks/useNutrition';
import { render, screen, fireEvent } from '../../../shared/utils/test-utils';

import { NutritionTab } from './NutritionTab';

// Mocks
vi.mock('../../../shared/hooks/useNutrition');

describe('NutritionTab', () => {
  const mockLogs = [
    { id: '1', date: '2024-01-01', calories: 2000, protein_grams: 150, carbs_grams: 200, fat_grams: 60, source: 'Manual' },
  ];

  const mockStats = {
    today: { calories: 1500, protein_grams: 100, carbs_grams: 150, fat_grams: 40 },
    daily_target: 2000,
    macro_targets: { protein: 150, carbs: 200, fat: 60 }
  };

  const defaultStore = {
    logs: [],
    stats: null,
    isLoading: false,
    error: null,
    page: 1,
    totalPages: 1,
    fetchLogs: vi.fn(),
    fetchStats: vi.fn(),
    deleteLog: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNutritionStore).mockReturnValue(defaultStore as any);
  });

  it('should call fetchLogs and fetchStats on mount', () => {
    render(<NutritionTab />);
    expect(defaultStore.fetchLogs).toHaveBeenCalled();
    expect(defaultStore.fetchStats).toHaveBeenCalled();
  });

  it('should not render macro widgets section', () => {
    vi.mocked(useNutritionStore).mockReturnValue({
      ...defaultStore,
      stats: mockStats,
    } as any);

    render(<NutritionTab />);
    expect(screen.queryByText(/^1500$/)).not.toBeInTheDocument();
    expect(screen.queryByText(/^100$/)).not.toBeInTheDocument();
  });

  it('should render logs list', () => {
    vi.mocked(useNutritionStore).mockReturnValue({
      ...defaultStore,
      logs: mockLogs,
      stats: mockStats,
    } as any);

    render(<NutritionTab />);
    // Check for the calorie value in the log card (2000 kcal). 
    // toLocaleString() in pt-BR might produce "2.000"
    expect(screen.getByText(/2.*000/)).toBeInTheDocument();
  });

  it('should not render AI quick action button', () => {
    render(<NutritionTab />);
    expect(screen.queryByText(/\(AI\)/i)).not.toBeInTheDocument();
  });

  it('should open manual add drawer when Registrar Refeicao clicked and keep button full width on mobile', () => {
    render(<NutritionTab />);
    const addBtn = screen.getByRole('button', { name: /Registrar Refeição/i });
    expect(addBtn.className).toContain('w-full');
    fireEvent.click(addBtn);
    // Use getAllByText and check the one that is a heading (h2)
    const titles = screen.getAllByText(/Registrar Refeição/i);
    expect(titles.some(t => t.tagName === 'H2')).toBe(true);
  });

  it('should open edit drawer when edit button clicked on log card', () => {
    vi.mocked(useNutritionStore).mockReturnValue({
      ...defaultStore,
      logs: mockLogs,
      stats: mockStats,
    } as any);

    render(<NutritionTab />);
    
    // Find edit button (Edit2 icon is usually rendered as a button with title or aria-label)
    // In NutritionLogCard it has title="Editar registro"
    const editBtn = screen.getByTitle(/Editar registro/i);
    fireEvent.click(editBtn);
    
    expect(screen.getByText(/Editar Refeição/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue('2000')).toBeInTheDocument();
  });

  it('should open view drawer when clicking on log card', () => {
    vi.mocked(useNutritionStore).mockReturnValue({
      ...defaultStore,
      logs: mockLogs,
      stats: mockStats,
    } as any);

    render(<NutritionTab />);
    
    const logCard = screen.getByTestId('nutrition-log-card');
    fireEvent.click(logCard);
    
    expect(screen.getByText(/Detalhes/i)).toBeInTheDocument();
    expect(screen.getByText('2000')).toBeInTheDocument();
  });
});
