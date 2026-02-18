import { render, screen, fireEvent } from '@testing-library/react';
import { renderHook } from '@testing-library/react';
import { useForm } from 'react-hook-form';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useNutritionTab } from '../hooks/useNutritionTab';

import { NutritionTab } from './NutritionTab';

// Mock hook
vi.mock('../hooks/useNutritionTab');

// Mock DateInput so Controller doesn't need a real form context
vi.mock('../../../shared/components/ui/DateInput', () => ({
  DateInput: ({ label }: { label?: string }) => <div data-testid="date-input">{label}</div>,
}));

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
  const mockCancelEdit = vi.fn();
  const mockChangePage = vi.fn();

  function makeMock(overrides: Partial<ReturnType<typeof useNutritionTab>> = {}): ReturnType<typeof useNutritionTab> {
    const { result } = renderHook(() => useForm());
    return {
      logs: [],
      stats: null,
      isLoading: false,
      isSaving: false,
      currentPage: 1,
      totalPages: 1,
      daysFilter: undefined,
      register: mockRegister,
      handleSubmit: mockHandleSubmit,
      control: result.current.control,
      errors: {},
      loadData: vi.fn(),
      deleteEntry: mockDeleteEntry,
      editEntry: vi.fn(),
      cancelEdit: mockCancelEdit,
      isEditing: false,
      editingId: null,
      setFilter: vi.fn(),
      nextPage: vi.fn(),
      prevPage: vi.fn(),
      changePage: mockChangePage,
      ...overrides,
    } as unknown as ReturnType<typeof useNutritionTab>;
  }

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNutritionTab).mockReturnValue(makeMock());
  });

  it('should render loading state', () => {
    vi.mocked(useNutritionTab).mockReturnValue(makeMock({ isLoading: true }));
    const { container } = render(<NutritionTab />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('should render form and log list', () => {
    const mockLogs = [{ id: '1', date: '2024-01-01', calories: 2000 }] as unknown as ReturnType<typeof useNutritionTab>['logs'];
    vi.mocked(useNutritionTab).mockReturnValue(makeMock({ logs: mockLogs }));

    render(<NutritionTab />);

    expect(screen.getByText('Registrar Dieta')).toBeInTheDocument();
    expect(screen.getByText('Histórico Recente')).toBeInTheDocument();
    expect(screen.getByText('2000 kcal')).toBeInTheDocument();
  });

  it('should call deleteEntry when delete button is clicked', () => {
    const mockLogs = [{ id: '1', date: '2024-01-01', calories: 2000 }] as unknown as ReturnType<typeof useNutritionTab>['logs'];
    vi.mocked(useNutritionTab).mockReturnValue(makeMock({ logs: mockLogs, deleteEntry: mockDeleteEntry }));

    render(<NutritionTab />);
    fireEvent.click(screen.getByText('Delete'));

    expect(mockDeleteEntry).toHaveBeenCalledWith('1');
  });

  it('should submit form', () => {
    render(<NutritionTab />);
    fireEvent.click(screen.getByText('Salvar Registro'));
    expect(mockHandleSubmit).toHaveBeenCalled();
  });

  it('should render empty state', () => {
    render(<NutritionTab />);
    expect(screen.getByText('Nenhum registro encontrado.')).toBeInTheDocument();
  });

  it('should show editing indicator and cancel button when isEditing is true', () => {
    vi.mocked(useNutritionTab).mockReturnValue(makeMock({ isEditing: true, editingId: 'abc123' }));

    render(<NutritionTab />);

    expect(screen.getByText('Editando Registro')).toBeInTheDocument();
    expect(screen.getByText('Cancelar')).toBeInTheDocument();
  });

  it('should call cancelEdit when cancel button is clicked', () => {
    vi.mocked(useNutritionTab).mockReturnValue(makeMock({ isEditing: true, editingId: 'abc123' }));

    render(<NutritionTab />);
    fireEvent.click(screen.getByText('Cancelar'));

    expect(mockCancelEdit).toHaveBeenCalled();
  });
});
