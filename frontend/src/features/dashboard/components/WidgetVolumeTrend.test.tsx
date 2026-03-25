import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { WidgetVolumeTrend } from './WidgetVolumeTrend';

// Mock recharts with all needed components
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: any }) => <div style={{ width: '100%', height: '100%' }}>{children}</div>,
  BarChart: ({ children }: { children: any }) => <svg>{children}</svg>,
  Bar: () => <g />,
  XAxis: () => <g />,
  YAxis: () => <g />,
  Tooltip: () => <div />,
  Cell: () => <g />,
  CartesianGrid: () => <g />,
}));

const mockData = [1000, 1200, 1100, 1300, 1400, 1350, 1500, 1600];

describe('WidgetVolumeTrend', () => {
  it('should render with overlay key if no data provided', () => {
    render(<WidgetVolumeTrend data={[]} />);
    expect(screen.getByText(/Volume Semanal/i)).toBeInTheDocument();
    expect(screen.getByText(/Histórico de volume indisponível/i)).toBeInTheDocument();
  });

  it('should render title and subtitle keys', () => {
    render(<WidgetVolumeTrend data={mockData} />);
    expect(screen.getByText(/Volume Semanal/i)).toBeInTheDocument();
    expect(screen.getByText(/Carga total levantada/i)).toBeInTheDocument();
  });
});
