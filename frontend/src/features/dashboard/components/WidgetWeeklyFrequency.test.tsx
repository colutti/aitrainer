import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { WidgetWeeklyFrequency } from './WidgetWeeklyFrequency';

describe('WidgetWeeklyFrequency', () => {
  const mockDays = [true, false, true, false, true, false, false];

  it('should render with overlay if days array is empty', () => {
    const { getByText } = render(<WidgetWeeklyFrequency days={[]} />);
    expect(getByText('Frequência Semanal')).toBeInTheDocument();
    expect(getByText('Nenhum treino esta semana')).toBeInTheDocument();
  });

  it('should render 7 day labels', () => {
    const { container } = render(<WidgetWeeklyFrequency days={mockDays} />);
    // Select the rounded-full divs that contain the day letters
    const dayBubbles = container.querySelectorAll('.rounded-full.flex.items-center.justify-center');
    expect(dayBubbles.length).toBe(7);
    expect(dayBubbles[0]).toHaveTextContent('S');
    expect(dayBubbles[6]).toHaveTextContent('D');
  });

  it('should apply active classes to active days', () => {
    const { container } = render(<WidgetWeeklyFrequency days={mockDays} />);
    const activeDays = container.querySelectorAll('.bg-emerald-500\\/20');
    expect(activeDays.length).toBe(3);
  });

  it('should apply inactive classes to inactive days', () => {
    const { container } = render(<WidgetWeeklyFrequency days={mockDays} />);
    const inactiveDays = container.querySelectorAll('.bg-white\\/5');
    expect(inactiveDays.length).toBe(4);
  });
});
