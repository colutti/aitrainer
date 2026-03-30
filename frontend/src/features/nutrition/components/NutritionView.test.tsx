import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { NutritionView } from './NutritionView';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      if (key === 'nutrition.weekly_days') return ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'];
      return key;
    },
  }),
}));

const mockLogs = [
  { 
    id: 'n1', 
    date: '2024-01-01T12:00:00Z', 
    calories: 600, 
    protein_grams: 40,
    carbs_grams: 60,
    fat_grams: 15,
  }
];

const mockStats = {
  today: { calories: 1200, protein_grams: 80, carbs_grams: 150, fat_grams: 40 },
  daily_target: 2000,
  macro_targets: { protein: 160, carbs: 200, fat: 60 },
  stability_score: 85,
  weekly_adherence: [true, true, true, false, true, false, false]
};

const mockProps = {
  logs: mockLogs as any,
  stats: mockStats as any,
  isLoading: false,
  onRegisterMeal: vi.fn(),
  onImport: vi.fn(),
  onDeleteLog: vi.fn(),
  isReadOnly: false,
  pagination: {
    currentPage: 1,
    totalPages: 1,
    onPageChange: vi.fn(),
  },
};

describe('NutritionView', () => {
  it('renders daily progress and macros correctly', () => {
    render(<NutritionView {...mockProps} />);
    // Check formatted calories 1.200
    expect(screen.getByText(/1\.200/)).toBeInTheDocument();
    // Check macros
    expect(screen.getByText(/80/)).toBeInTheDocument(); 
    expect(screen.getByText(/150/)).toBeInTheDocument();
  });

  it('renders adherence score', () => {
    render(<NutritionView {...mockProps} />);
    expect(screen.getByText(/85%/)).toBeInTheDocument();
  });

  it('renders meal history list', () => {
    render(<NutritionView {...mockProps} />);
    // Check for formatted date or calories in history
    expect(screen.getByText(/600/)).toBeInTheDocument();
  });

  it('calls onRegisterMeal when button clicked', () => {
    render(<NutritionView {...mockProps} />);
    const addBtn = screen.getByText(/nutrition\.register_meal/i);
    fireEvent.click(addBtn);
    expect(mockProps.onRegisterMeal).toHaveBeenCalled();
  });

  it('renders pagination and advances pages', () => {
    render(
      <NutritionView
        {...mockProps}
        pagination={{ currentPage: 2, totalPages: 5, onPageChange: mockProps.pagination.onPageChange }}
      />
    );

    expect(screen.getByText((_content, element) => element?.textContent === '2 / 5')).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText(/Próxima/i));
    expect(mockProps.pagination.onPageChange).toHaveBeenCalledWith(3);
  });

  it('disables actions in read-only mode', () => {
    render(<NutritionView {...mockProps} isReadOnly />);
    expect(screen.getByRole('button', { name: /nutrition\.register_meal/i })).toBeDisabled();
    expect(screen.queryByLabelText(/Delete/i)).not.toBeInTheDocument();
  });
});
