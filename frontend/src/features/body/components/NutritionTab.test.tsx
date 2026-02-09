import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useNutritionTab } from '../hooks/useNutritionTab';

import { NutritionTab } from './NutritionTab';

// Mock hook
vi.mock('../hooks/useNutritionTab');

// Mock child component
vi.mock('../../nutrition/components/NutritionLogCard', () => ({
  NutritionLogCard: ({ log, onDelete }: { log: { calories: number; id: string }; onDelete: (id: string) => void }) => (
    <div data-testid="nutrition-log-card">
      <span>{log.calories} kcal</span>
      <button onClick={() => { onDelete(log.id); }}>Delete</button>
    </div>
  ),
}));

describe('NutritionTab', () => {
  const mockRegister = vi.fn();
  const mockHandleSubmit = vi.fn((fn: () => void) => (e?: { preventDefault: () => void }) => {
    e?.preventDefault();
    fn();
  });
  const mockDeleteEntry = vi.fn();
  const mockChangePage = vi.fn();

  const defaultHookValues = {
    logs: [],
    stats: null,
    isLoading: false,
    isSaving: false,
    currentPage: 1,
    totalPages: 1,
    daysFilter: undefined,
    register: mockRegister,
    handleSubmit: mockHandleSubmit,
    errors: {},
    loadData: vi.fn(),
    deleteEntry: mockDeleteEntry,
    editEntry: vi.fn(),
    setFilter: vi.fn(),
    nextPage: vi.fn(),
    prevPage: vi.fn(),
    changePage: mockChangePage,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNutritionTab).mockReturnValue(defaultHookValues as unknown as ReturnType<typeof useNutritionTab>);
  });

  it('should render loading state', () => {
    vi.mocked(useNutritionTab).mockReturnValue({
      ...defaultHookValues,
      isLoading: true,
      logs: [],
    } as unknown as ReturnType<typeof useNutritionTab>);

    const { container } = render(<NutritionTab />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('should render form and log list', () => {
    const mockLogs = [{ id: '1', date: '2024-01-01', calories: 2000 }];
    vi.mocked(useNutritionTab).mockReturnValue({
      ...defaultHookValues,
      logs: mockLogs,
    } as unknown as ReturnType<typeof useNutritionTab>);

    render(<NutritionTab />);
    
    expect(screen.getByText('Registrar Dieta')).toBeInTheDocument();
    expect(screen.getByText('Histórico Recente')).toBeInTheDocument();
    expect(screen.getByText('2000 kcal')).toBeInTheDocument();
  });

  it('should call deleteEntry when delete button is clicked', () => {
    const mockLogs = [{ id: '1', date: '2024-01-01', calories: 2000 }];
    vi.mocked(useNutritionTab).mockReturnValue({
      ...defaultHookValues,
      logs: mockLogs,
    } as unknown as ReturnType<typeof useNutritionTab>);

    render(<NutritionTab />);
    
    const deleteBtn = screen.getByText('Delete');
    fireEvent.click(deleteBtn);
    
    expect(mockDeleteEntry).toHaveBeenCalledWith('1');
  });

  it('should submit form', () => {
    render(<NutritionTab />);
    
    const submitBtn = screen.getByText('Salvar Registro');
    fireEvent.click(submitBtn);

    expect(mockHandleSubmit).toHaveBeenCalled();
  });

  it('should render empty state', () => {
    render(<NutritionTab />);
    expect(screen.getByText('Nenhum registro encontrado.')).toBeInTheDocument();
  });
});
