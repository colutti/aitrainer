import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { WidgetWeeklyFrequency } from './WidgetWeeklyFrequency';

describe('WidgetWeeklyFrequency', () => {
  it('should render with overlay if days array is empty', () => {
    const { getByText } = render(<WidgetWeeklyFrequency days={[]} />);
    // Verifica se renderiza as chaves de tradução
    expect(getByText(/Frequência/i)).toBeInTheDocument();
    expect(getByText(/Nenhum treino esta semana/i)).toBeInTheDocument();
  });

  it('should render 7 day bubbles', () => {
    const { container } = render(<WidgetWeeklyFrequency days={[true, false, true, false, true, false, true]} />);
    // Busca pelas bolhas de dia (pelo estilo/estrutura)
    const dayBubbles = container.querySelectorAll('.rounded-full.flex.items-center');
    expect(dayBubbles.length).toBe(7);
  });
});
