import { render, screen, fireEvent } from '@testing-library/react';
import { renderHook } from '@testing-library/react';
import { useForm } from 'react-hook-form';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useWeightTab } from '../hooks/useWeightTab';

import { WeightTab } from './WeightTab';

// Mock hook
vi.mock('../hooks/useWeightTab');

// Mock DateInput so Controller doesn't need a real form context
vi.mock('../../../shared/components/ui/DateInput', () => ({
  DateInput: ({ label }: { label?: string }) => <div data-testid="date-input">{label}</div>,
}));

// Mock components to simplify test
vi.mock('./WeightLogCard', () => ({
  WeightLogCard: ({ log, onDelete, onEdit }: { log: { weight_kg: number; date: string; id: string }; onDelete: (date: string) => void; onEdit: (log: unknown) => void }) => (
    <div data-testid="weight-log-card">
      <span>{log.weight_kg} kg</span>
      <button onClick={() => { onDelete(log.date); }}>Delete</button>
      <button onClick={() => { onEdit(log); }}>Edit</button>
    </div>
  ),
}));

vi.mock('./WeightLogDrawer', () => ({
  WeightLogDrawer: () => <div data-testid="weight-log-drawer" />,
}));

describe('WeightTab', () => {
  const mockRegister = vi.fn();
  const mockHandleSubmit = vi.fn((fn: () => void) => (e?: { preventDefault: () => void }) => {
    e?.preventDefault();
    fn();
  });
  const mockDeleteEntry = vi.fn();
  const mockEditEntry = vi.fn();
  const mockChangePage = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    // Use renderHook to get a real control object (required by Controller)
    const { result } = renderHook(() => useForm());
    const control = result.current.control;

    vi.mocked(useWeightTab).mockReturnValue({
      history: [],
      stats: null,
      isLoading: false,
      isSaving: false,
      register: mockRegister,
      handleSubmit: mockHandleSubmit,
      control,
      errors: {},
      loadData: vi.fn(),
      deleteEntry: mockDeleteEntry,
      editEntry: mockEditEntry,
      page: 1,
      totalPages: 1,
      changePage: mockChangePage,
    } as unknown as ReturnType<typeof useWeightTab>);
  });

  it('should render loading state initially', () => {
    const { result } = renderHook(() => useForm());
    vi.mocked(useWeightTab).mockReturnValue({
      history: [],
      stats: null,
      isLoading: true,
      isSaving: false,
      register: mockRegister,
      handleSubmit: mockHandleSubmit,
      control: result.current.control,
      errors: {},
      loadData: vi.fn(),
      deleteEntry: mockDeleteEntry,
      editEntry: mockEditEntry,
      page: 1,
      totalPages: 1,
      changePage: mockChangePage,
    } as unknown as ReturnType<typeof useWeightTab>);

    const { container } = render(<WeightTab />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('should render form and history list', () => {
    const { result } = renderHook(() => useForm());
    const mockHistory = [{ id: '1', date: '2024-01-01', weight_kg: 80 }];
    vi.mocked(useWeightTab).mockReturnValue({
      history: mockHistory,
      stats: null,
      isLoading: false,
      isSaving: false,
      register: mockRegister,
      handleSubmit: mockHandleSubmit,
      control: result.current.control,
      errors: {},
      loadData: vi.fn(),
      deleteEntry: mockDeleteEntry,
      editEntry: mockEditEntry,
      page: 1,
      totalPages: 1,
      changePage: mockChangePage,
    } as unknown as ReturnType<typeof useWeightTab>);

    render(<WeightTab />);

    expect(screen.getByText('Registrar Peso')).toBeInTheDocument();
    expect(screen.getByText('Histórico Recente')).toBeInTheDocument();
    expect(screen.getByText('80 kg')).toBeInTheDocument();
  });

  it('should call deleteEntry when delete button is clicked', () => {
    const { result } = renderHook(() => useForm());
    const mockHistory = [{ id: '1', date: '2024-01-01', weight_kg: 80 }];
    vi.mocked(useWeightTab).mockReturnValue({
      history: mockHistory,
      stats: null,
      isLoading: false,
      isSaving: false,
      register: mockRegister,
      handleSubmit: mockHandleSubmit,
      control: result.current.control,
      errors: {},
      loadData: vi.fn(),
      deleteEntry: mockDeleteEntry,
      editEntry: mockEditEntry,
      page: 1,
      totalPages: 1,
      changePage: mockChangePage,
    } as unknown as ReturnType<typeof useWeightTab>);

    render(<WeightTab />);

    const deleteBtn = screen.getByText('Delete');
    fireEvent.click(deleteBtn);

    expect(mockDeleteEntry).toHaveBeenCalledWith('2024-01-01');
  });

  it('should call editEntry when edit button is clicked', () => {
    const { result } = renderHook(() => useForm());
    const mockHistory = [{ id: '1', date: '2024-01-01', weight_kg: 80 }];
    vi.mocked(useWeightTab).mockReturnValue({
      history: mockHistory,
      stats: null,
      isLoading: false,
      isSaving: false,
      register: mockRegister,
      handleSubmit: mockHandleSubmit,
      control: result.current.control,
      errors: {},
      loadData: vi.fn(),
      deleteEntry: mockDeleteEntry,
      editEntry: mockEditEntry,
      page: 1,
      totalPages: 1,
      changePage: mockChangePage,
    } as unknown as ReturnType<typeof useWeightTab>);

    render(<WeightTab />);

    const editBtn = screen.getByText('Edit');
    fireEvent.click(editBtn);

    expect(mockEditEntry).toHaveBeenCalledWith(mockHistory[0]);
  });

  it('should submit form', () => {
    render(<WeightTab />);

    const submitBtn = screen.getByText('Salvar Registro');
    fireEvent.click(submitBtn);

    expect(mockHandleSubmit).toHaveBeenCalled();
  });

  it('should render empty state when no history', () => {
    render(<WeightTab />);
    expect(screen.getByText('Nenhum registro encontrado.')).toBeInTheDocument();
  });
});
