import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { WidgetVolumeTrend } from './WidgetVolumeTrend';

// Mock recharts
vi.mock('recharts', () => {
  return {
    ResponsiveContainer: ({ children }: any) => <div style={{ width: '100%', height: '100%' }}>{children}</div>,
    BarChart: ({ children }: any) => <svg>{children}</svg>,
    Bar: () => <g />,
    XAxis: () => <g />,
    YAxis: () => <g />,
    CartesianGrid: () => <g />,
    Tooltip: () => <div />,
  };
});

describe('WidgetVolumeTrend', () => {
  const mockData = [1000, 2000, 1500, 2500];

  it('should render nothing if no data provided', () => {
    const { container } = render(<WidgetVolumeTrend data={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('should render title and subtitle', () => {
    render(<WidgetVolumeTrend data={mockData} />);
    expect(screen.getByText('Tendência de Volume')).toBeInTheDocument();
    expect(screen.getByText('Últimas 8 semanas')).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(<WidgetVolumeTrend data={mockData} className="custom-volume" />);
    expect(container.firstChild).toHaveClass('custom-volume');
  });
});
