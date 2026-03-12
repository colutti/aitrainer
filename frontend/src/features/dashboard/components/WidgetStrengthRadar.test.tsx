import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { WidgetStrengthRadar } from './WidgetStrengthRadar';

// Mock recharts
vi.mock('recharts', () => {
  const OriginalModule = vi.importActual('recharts');
  return {
    ...OriginalModule,
    ResponsiveContainer: ({ children }: any) => <div style={{ width: '100%', height: '100%' }}>{children}</div>,
    RadarChart: ({ children }: any) => <svg>{children}</svg>,
    PolarGrid: () => <g />,
    PolarAngleAxis: () => <g />,
    PolarRadiusAxis: () => <g />,
    Radar: () => <g />,
  };
});

describe('WidgetStrengthRadar', () => {
  const mockData = {
    push: 0.8,
    pull: 0.7,
    legs: 0.9,
    core: 0.5,
  };

  it('should render title and subtitle', () => {
    render(<WidgetStrengthRadar data={mockData} />);
    expect(screen.getByText('Balanço de Força')).toBeInTheDocument();
    expect(screen.getByText('Equilíbrio por Categoria')).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(<WidgetStrengthRadar data={mockData} className="custom-radar" />);
    expect(container.firstChild).toHaveClass('custom-radar');
  });
});
