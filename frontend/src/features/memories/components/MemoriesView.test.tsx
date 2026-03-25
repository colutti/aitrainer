import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { MemoriesView } from './MemoriesView';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'pt-BR' }
  }),
}));

const mockMemories = [
  { id: 'm1', memory: 'Usuário prefere treinar de manhã', created_at: '2024-01-01T10:00:00Z', updated_at: '2024-01-01T10:00:00Z' },
  { id: 'm2', memory: 'Alergia a amendoim', created_at: '2024-01-02T10:00:00Z', updated_at: '2024-01-02T10:00:00Z' }
];

const mockProps = {
  memories: mockMemories,
  isLoading: false,
  totalMemories: 2,
  currentPage: 1,
  totalPages: 1,
  onDelete: vi.fn(),
  onPageChange: vi.fn(),
};

describe('MemoriesView', () => {
  it('renders memory list correctly', () => {
    render(<MemoriesView {...mockProps} />);
    expect(screen.getByText('Usuário prefere treinar de manhã')).toBeInTheDocument();
    expect(screen.getByText('Alergia a amendoim')).toBeInTheDocument();
  });

  it('renders stats summary', () => {
    render(<MemoriesView {...mockProps} />);
    expect(screen.getByText('2')).toBeInTheDocument(); // totalInsights
  });

  it('calls onDelete when delete button is clicked', () => {
    render(<MemoriesView {...mockProps} />);
    const deleteBtns = screen.getAllByLabelText('shared.delete');
    fireEvent.click(deleteBtns[0]!);
    expect(mockProps.onDelete).toHaveBeenCalledWith('m1');
  });

  it('renders empty state when no memories', () => {
    render(<MemoriesView {...mockProps} memories={[]} />);
    expect(screen.getByText('memories.empty_title')).toBeInTheDocument();
  });
});
