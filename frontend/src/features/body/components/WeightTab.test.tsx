import { render, screen, fireEvent, renderHook } from '@testing-library/react';
import { useForm } from 'react-hook-form';
import { MemoryRouter } from 'react-router-dom';
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
  WeightLogDrawer: ({ isOpen, log, mode, handleSubmit, onSubmit, onClose, onCancelEdit }: any) => {
    if (!isOpen) return <div data-testid={`weight-log-drawer-${mode}`} />;
    return (
      <div data-testid={`weight-log-drawer-${mode}`}>
        <div data-testid="drawer-open">Open</div>
        {mode === 'edit' && log && <div data-testid="edit-mode">Editando Registro</div>}
        {mode === 'edit' && (
          <form onSubmit={(e) => { if (handleSubmit && onSubmit) handleSubmit(onSubmit)(e); }}>
            <button type="submit">Save</button>
          </form>
        )}
        <button onClick={onCancelEdit ?? onClose}>Cancelar</button>
      </div>
    );
  },
}));

describe('WeightTab', () => {
  const mockRegister = vi.fn();
  const mockHandleSubmit = vi.fn((fn: () => void) => (e?: { preventDefault: () => void }) => {
    e?.preventDefault();
    fn();
  });
  const mockDeleteEntry = vi.fn();
  const mockEditEntry = vi.fn();
  const mockCancelEdit = vi.fn();
  const mockChangePage = vi.fn();

  function makeMock(overrides: Partial<ReturnType<typeof useWeightTab>> = {}): ReturnType<typeof useWeightTab> {
    const { result } = renderHook(() => useForm());
    return {
      history: [],
      stats: null,
      isLoading: false,
      isSaving: false,
      register: mockRegister,
      handleSubmit: mockHandleSubmit,
      onSubmit: vi.fn(),
      control: result.current.control,
      errors: {},
      loadData: vi.fn(),
      deleteEntry: mockDeleteEntry,
      editEntry: mockEditEntry,
      cancelEdit: mockCancelEdit,
      isEditing: false,
      editingDate: null,
      page: 1,
      totalPages: 1,
      changePage: mockChangePage,
      ...overrides,
    } as unknown as ReturnType<typeof useWeightTab>;
  }

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useWeightTab).mockReturnValue(makeMock());
  });

  it('should render loading state initially', () => {
    vi.mocked(useWeightTab).mockReturnValue(makeMock({ isLoading: true }));
    const { container } = render(<MemoryRouter><WeightTab /></MemoryRouter>);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('should render form and history list', () => {
    const mockHistory = [{ id: '1', date: '2024-01-01', weight_kg: 80 }] as unknown as ReturnType<typeof useWeightTab>['history'];
    vi.mocked(useWeightTab).mockReturnValue(makeMock({ history: mockHistory }));

    render(<MemoryRouter><WeightTab /></MemoryRouter>);

    expect(screen.getByText('Registrar Peso')).toBeInTheDocument();
    expect(screen.getByText('Histórico Recente')).toBeInTheDocument();
    expect(screen.getByText('80 kg')).toBeInTheDocument();
  });

  it('should call deleteEntry when delete button is clicked', () => {
    const mockHistory = [{ id: '1', date: '2024-01-01', weight_kg: 80 }] as unknown as ReturnType<typeof useWeightTab>['history'];
    vi.mocked(useWeightTab).mockReturnValue(makeMock({ history: mockHistory }));

    render(<MemoryRouter><WeightTab /></MemoryRouter>);
    fireEvent.click(screen.getByText('Delete'));

    expect(mockDeleteEntry).toHaveBeenCalledWith('2024-01-01');
  });

  it('should call editEntry when edit button is clicked', () => {
    const mockHistory = [{ id: '1', date: '2024-01-01', weight_kg: 80 }] as unknown as ReturnType<typeof useWeightTab>['history'];
    vi.mocked(useWeightTab).mockReturnValue(makeMock({ history: mockHistory }));

    render(<MemoryRouter><WeightTab /></MemoryRouter>);
    fireEvent.click(screen.getByText('Edit'));

    expect(mockEditEntry).toHaveBeenCalledWith(mockHistory[0]);
  });

  it('should submit form', () => {
    render(<MemoryRouter><WeightTab /></MemoryRouter>);
    fireEvent.click(screen.getByText('Registrar Peso')); // Open the drawer
    const form = screen.getByTestId('weight-log-drawer-edit').querySelector('form'); // Get the form inside the drawer
    if (form) fireEvent.submit(form);
    expect(mockHandleSubmit).toHaveBeenCalled();
  });

  it('should render empty state when no history', () => {
    vi.mocked(useWeightTab).mockReturnValue(makeMock({ history: [] }));
    render(<MemoryRouter><WeightTab /></MemoryRouter>);
    expect(screen.getByText('Nenhum registro encontrado.')).toBeInTheDocument();
  });

  it('should show editing indicator and cancel button when isEditing is true', () => {
    const mockLog = { id: '1', date: '2024-01-15', weight_kg: 75 };
    vi.mocked(useWeightTab).mockReturnValue(makeMock({ 
      isEditing: true, 
      editingDate: '2024-01-15',
      history: [mockLog] as any
    }));

    render(<MemoryRouter><WeightTab /></MemoryRouter>);
    fireEvent.click(screen.getByText('Registrar Peso')); // Open the drawer

    expect(screen.getByTestId('edit-mode')).toHaveTextContent('Editando Registro');
    expect(screen.getByText('Cancelar')).toBeInTheDocument();
  });

  it('should call cancelEdit when cancel button is clicked', () => {
    vi.mocked(useWeightTab).mockReturnValue(makeMock({ isEditing: true, editingDate: '2024-01-15' }));

    render(<MemoryRouter><WeightTab /></MemoryRouter>);
    fireEvent.click(screen.getByText('Registrar Peso')); // Open the drawer
    fireEvent.click(screen.getByText('Cancelar'));

    expect(mockCancelEdit).toHaveBeenCalled();
  });
});
