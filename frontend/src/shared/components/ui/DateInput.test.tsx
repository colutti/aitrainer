import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { DateInput } from './DateInput';

describe('DateInput', () => {
  it('exibe placeholder quando sem valor', () => {
    render(<DateInput label="Data" onChange={vi.fn()} />);
    expect(screen.getByText('DD/MM/AAAA')).toBeInTheDocument();
  });

  it('exibe data em formato DD/MM/AAAA quando valor fornecido', () => {
    render(<DateInput label="Data" value="2026-02-18" onChange={vi.fn()} />);
    expect(screen.getByText('18/02/2026')).toBeInTheDocument();
  });

  it('abre calendário ao clicar', async () => {
    const user = userEvent.setup();
    render(<DateInput label="Data" onChange={vi.fn()} />);
    await user.click(screen.getByRole('button'));
    expect(screen.getByRole('grid')).toBeInTheDocument();
  });

  it('chama onChange com formato YYYY-MM-DD ao selecionar data', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<DateInput label="Data" value="2026-02-18" onChange={onChange} />);
    await user.click(screen.getByRole('button'));
    // Agora buscamos os buttons dentro do calendário (todos os botões exceto o primeiro que abre o calendário)
    const allButtons = screen.getAllByRole('button');
    // Ignorar o primeiro button (que abre/fecha o calendário)
    const dayButton = allButtons.slice(1).find(b => b.textContent === '10');
    expect(dayButton).toBeDefined();
    if (dayButton) await user.click(dayButton);
    expect(onChange).toHaveBeenCalledWith('2026-02-10');
  });

  it('exibe mensagem de erro quando passada', () => {
    render(<DateInput label="Data" error="Data obrigatória" onChange={vi.fn()} />);
    expect(screen.getByText('Data obrigatória')).toBeInTheDocument();
  });
});
