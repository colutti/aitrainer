import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useWeightTab } from '../hooks/useWeightTab';

import { WeightTab } from './WeightTab';

// Mock hook
vi.mock('../hooks/useWeightTab');

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

  const defaultHookValues = {
    history: [],
    stats: null,
    isLoading: false,
    isSaving: false,
    register: mockRegister,
    handleSubmit: mockHandleSubmit,
    errors: {},
    loadData: vi.fn(),
    deleteEntry: mockDeleteEntry,
    editEntry: mockEditEntry,
    page: 1,
    totalPages: 1,
    changePage: mockChangePage,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useWeightTab).mockReturnValue(defaultHookValues as unknown as ReturnType<typeof useWeightTab>);
  });

  it('should render loading state initially', () => {
    vi.mocked(useWeightTab).mockReturnValue({
      ...defaultHookValues,
      isLoading: true,
      history: [],
    } as unknown as ReturnType<typeof useWeightTab>);

    const { container } = render(<WeightTab />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('should render form and history list', () => {
    const mockHistory = [{ id: '1', date: '2024-01-01', weight_kg: 80 }];
    vi.mocked(useWeightTab).mockReturnValue({
      ...defaultHookValues,
      history: mockHistory,
    } as unknown as ReturnType<typeof useWeightTab>);

    render(<WeightTab />);
    
    expect(screen.getByText('Registrar Peso')).toBeInTheDocument();
    expect(screen.getByText('Histórico Recente')).toBeInTheDocument();
    expect(screen.getByText('80 kg')).toBeInTheDocument(); // From mocked Card
  });

  it('should call deleteEntry when delete button is clicked', () => {
    const mockHistory = [{ id: '1', date: '2024-01-01', weight_kg: 80 }];
    vi.mocked(useWeightTab).mockReturnValue({
      ...defaultHookValues,
      history: mockHistory,
    } as unknown as ReturnType<typeof useWeightTab>);

    render(<WeightTab />);
    
    const deleteBtn = screen.getByText('Delete');
    fireEvent.click(deleteBtn);
    
    expect(mockDeleteEntry).toHaveBeenCalledWith('2024-01-01');
  });

  it('should call editEntry when edit button is clicked', () => {
    const mockHistory = [{ id: '1', date: '2024-01-01', weight_kg: 80 }];
    vi.mocked(useWeightTab).mockReturnValue({
      ...defaultHookValues,
      history: mockHistory,
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
