import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { DashboardMiniChart } from './DashboardMiniChart';

describe('DashboardMiniChart', () => {
  it('keeps the chart in flow on mobile and absolute on md screens', () => {
    const { container } = render(
      <DashboardMiniChart
        data={[
          { date: '2024-01-01', value: 10 },
          { date: '2024-01-02', value: 11 },
        ]}
        dataKey="value"
        color="#10b981"
        id="weight"
      />
    );

    const wrapper = container.firstElementChild as HTMLElement | null;
    expect(wrapper?.className).toContain('mt-auto');
    expect(wrapper?.className).not.toContain('md:absolute');
    expect(wrapper?.className).toContain('h-24');
    expect(wrapper?.className).toContain('pointer-events-none');
    expect(wrapper?.className).toContain('-mx-6');
    expect(wrapper?.className).toContain('-mb-6');
  });

  it('renders nothing without data', () => {
    const { container } = render(
      <DashboardMiniChart data={[]} dataKey="value" color="#10b981" id="weight" />
    );

    expect(container).toBeEmptyDOMElement();
  });
});
