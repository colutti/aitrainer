import { render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { WidgetWeightChart } from './WidgetWeightChart';

// Mock recharts
vi.mock('recharts', () => {
  return {
    ResponsiveContainer: ({ children }: any) => <div style={{ width: '100%', height: '100%' }}>{children}</div>,
    AreaChart: ({ children }: any) => <svg>{children}</svg>,
    Area: () => <g />,
    YAxis: () => <g />,
    Tooltip: () => <div />,
  };
});

describe('WidgetWeightChart', () => {
  const mockData = [
    { date: '2024-01-01', weight: 80 },
    { date: '2024-01-02', weight: 79.5 },
    { date: '2024-01-03', weight: 79.8 },
  ];

  it('should render nothing if no data provided', () => {
    const { container } = render(<WidgetWeightChart data={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('should render SVG chart when data is provided', () => {
    const { container } = render(<WidgetWeightChart data={mockData} />);
    expect(container.querySelector('svg')).toBeInTheDocument();
  });
});
