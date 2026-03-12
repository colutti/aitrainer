import { render, screen, fireEvent } from '@testing-library/react';
import { useTranslation } from 'react-i18next';
import { describe, expect, it, vi } from 'vitest';

import { LanguageSelector } from './LanguageSelector';

// Mock translation hook
vi.mock('react-i18next', () => ({
  useTranslation: vi.fn(),
}));

describe('LanguageSelector', () => {
  const i18nMock = {
    language: 'pt-BR',
    changeLanguage: vi.fn().mockResolvedValue(undefined),
  };

  vi.mocked(useTranslation).mockReturnValue({
    t: (key: string) => key,
    i18n: i18nMock as any,
  } as any);

  it('should render initial language abbreviation', () => {
    render(<LanguageSelector />);
    expect(screen.getByText('PT')).toBeInTheDocument();
  });

  it('should open dropdown on click and show languages', async () => {
    render(<LanguageSelector />);
    const toggleButton = screen.getByRole('button');
    fireEvent.click(toggleButton);

    expect(screen.getByText('Português')).toBeInTheDocument();
    expect(screen.getByText('Español')).toBeInTheDocument();
    expect(screen.getByText('English')).toBeInTheDocument();
  });

  it('should call i18n.changeLanguage when a language is clicked', async () => {
    render(<LanguageSelector />);
    const toggleButton = screen.getByRole('button');
    fireEvent.click(toggleButton);

    const spanishButton = screen.getByText('Español');
    fireEvent.click(spanishButton);

    expect(i18nMock.changeLanguage).toHaveBeenCalledWith('es-ES');
  });

  it('should close dropdown after selection', async () => {
    render(<LanguageSelector />);
    const toggleButton = screen.getByRole('button');
    fireEvent.click(toggleButton);

    const englishButton = screen.getByText('English');
    fireEvent.click(englishButton);

    expect(screen.queryByText('English')).not.toBeInTheDocument();
  });

  it('should close dropdown on outside click', async () => {
    render(<LanguageSelector />);
    const toggleButton = screen.getByRole('button');
    fireEvent.click(toggleButton);

    // Simulate outside click
    fireEvent.mouseDown(document.body);

    expect(screen.queryByText('Português')).not.toBeInTheDocument();
  });
});
