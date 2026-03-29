import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { MemoriesView } from './MemoriesView';

const useTranslationMock = vi.fn();

vi.mock('react-i18next', () => ({
  useTranslation: () => useTranslationMock(),
}));

const mockMemories = [
  {
    id: 'm1',
    memory: 'User prefers morning training',
    translations: { 'pt-BR': 'Usuário prefere treinar de manhã' },
    created_at: '2024-01-01T10:00:00Z',
    updated_at: '2024-01-01T10:00:00Z'
  },
  {
    id: 'm2',
    memory: 'Peanut allergy',
    translations: { 'pt-BR': 'Alergia a amendoim' },
    created_at: '2024-01-02T10:00:00Z',
    updated_at: '2024-01-02T10:00:00Z'
  }
];

const mockProps = {
  memories: mockMemories,
  isLoading: false,
  totalMemories: 2,
  currentPage: 1,
  totalPages: 1,
  isReadOnly: false,
  onDelete: vi.fn(),
  onPageChange: vi.fn(),
};

describe('MemoriesView', () => {
  beforeEach(() => {
    useTranslationMock.mockReturnValue({
      t: (key: string) => key,
      i18n: { language: 'pt-BR' }
    });
  });

  it('renders memory list correctly', () => {
    render(<MemoriesView {...mockProps} />);
    expect(screen.getByText('Usuário prefere treinar de manhã')).toBeInTheDocument();
    expect(screen.getByText('Alergia a amendoim')).toBeInTheDocument();
  });

  it('falls back to english when the locale has no translation', () => {
    useTranslationMock.mockReturnValueOnce({
      t: (key: string) => key,
      i18n: { language: 'en-US' }
    });

    render(<MemoriesView {...mockProps} />);
    expect(screen.getByText('User prefers morning training')).toBeInTheDocument();
    expect(screen.getByText('Peanut allergy')).toBeInTheDocument();
  });

  it('disables delete actions in read-only mode', () => {
    render(<MemoriesView {...mockProps} isReadOnly />);
    expect(screen.getByText('Demo Read-Only')).toBeInTheDocument();
    expect(screen.getAllByLabelText('shared.delete')[0]).toBeDisabled();
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
