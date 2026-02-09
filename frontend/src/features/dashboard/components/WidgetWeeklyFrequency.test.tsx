import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { WidgetWeeklyFrequency } from './WidgetWeeklyFrequency';

describe('WidgetWeeklyFrequency', () => {
  const mockDays = [true, false, true, false, true, false, false];

  it('should render nothing if days length is not 7', () => {
    const { container } = render(<WidgetWeeklyFrequency days={[true]} />);
    expect(container.firstChild).toBeNull();
  });

  it('should render 7 day labels', () => {
    const { container } = render(<WidgetWeeklyFrequency days={mockDays} />);
    // Select the rounded-full divs that contain the day letters
    const dayBubbles = container.querySelectorAll('.rounded-full.w-8.h-8');
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
