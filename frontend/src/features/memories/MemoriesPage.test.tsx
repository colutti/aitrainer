import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useConfirmation } from '../../shared/hooks/useConfirmation';
import { useMemoryStore } from '../../shared/hooks/useMemory';

import MemoriesPage from './MemoriesPage';

vi.mock('../../shared/hooks/useMemory');
vi.mock('../../shared/hooks/useConfirmation');
vi.mock('../../shared/hooks/useNotification', () => ({
  useNotificationStore: () => ({
    success: vi.fn(),
    error: vi.fn(),
  }),
}));

describe('MemoriesPage', () => {
  const mockFetchMemories = vi.fn();
  const mockDeleteMemory = vi.fn();
  const mockNextPage = vi.fn();
  const mockPrevPage = vi.fn();
  const mockConfirm = vi.fn();

  const defaultStore = {
    memories: [],
    isLoading: false,
    currentPage: 1,
    totalPages: 1,
    totalMemories: 0,
    fetchMemories: mockFetchMemories,
    deleteMemory: mockDeleteMemory,
    nextPage: mockNextPage,
    previousPage: mockPrevPage,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useMemoryStore).mockReturnValue(defaultStore);
    vi.mocked(useConfirmation).mockReturnValue({ confirm: mockConfirm });
  });

  it('should render empty state', () => {
    render(<MemoriesPage />);
    expect(screen.getByText('Nenhuma memória capturada ainda.')).toBeInTheDocument();
  });

  it('should render memories list', () => {
    vi.mocked(useMemoryStore).mockReturnValue({
      ...defaultStore,
      memories: [
        { id: '1', memory: 'User likes pizza', created_at: '2024-01-01' },
        { id: '2', memory: 'User dislikes broccoli', created_at: '2024-01-02' },
      ],
      totalMemories: 2,
    });

    render(<MemoriesPage />);
    expect(screen.getByText('User likes pizza')).toBeInTheDocument();
    expect(screen.getByText('User dislikes broccoli')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // Total Insights count
  });

  it('should handle delete interaction', async () => {
    vi.mocked(useMemoryStore).mockReturnValue({
      ...defaultStore,
      memories: [
        { id: '1', memory: 'User likes pizza', created_at: '2024-01-01' },
      ],
    });
    mockConfirm.mockResolvedValue(true);

    render(<MemoriesPage />);

    fireEvent.click(screen.getByLabelText(/Excluir|Delete/i));

    expect(mockConfirm).toHaveBeenCalled();
    await waitFor(() => {
      expect(mockDeleteMemory).toHaveBeenCalledWith('1');
    });
  });
  
  it('should handle pagination', () => {
     vi.mocked(useMemoryStore).mockReturnValue({
      ...defaultStore,
      memories: [{ id: 'memory-1', memory: 'Test memory', created_at: '2024-01-01' }],
      currentPage: 1,
      totalPages: 2,
    });
    
    render(<MemoriesPage />);
    
    // The pagination component uses lucide-react chevron icons, usually wrapped in buttons
    // Let's grab the next button via aria-label or role if text isn't explicit
    const buttons = screen.getAllByRole('button');
    // The next button is typically the last button in the pagination controls
    const nextBtn = buttons[buttons.length - 1];
    if (nextBtn) {
      fireEvent.click(nextBtn);
    }
    expect(mockNextPage).toHaveBeenCalled();
  });
});
