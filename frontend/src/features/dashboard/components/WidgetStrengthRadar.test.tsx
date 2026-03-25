import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { WidgetStrengthRadar } from './WidgetStrengthRadar';

// Mock recharts
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: any }) => <div style={{ width: '100%', height: '100%' }}>{children}</div>,
  RadarChart: ({ children }: { children: any }) => <svg>{children}</svg>,
  PolarGrid: () => <g />,
  PolarAngleAxis: () => <g />,
  PolarRadiusAxis: () => <g />,
  Radar: () => <g />,
}));

const mockData: any = {
  push: 80,
  pull: 70,
  legs: 90,
  labels: ['Peito', 'Costas', 'Pernas', 'Ombros', 'Braços'],
  values: [80, 70, 90, 60, 75],
};

describe('WidgetStrengthRadar', () => {
  it('should render title and subtitle keys', () => {
    render(<WidgetStrengthRadar data={mockData} />);
    expect(screen.getByText(/Equilíbrio de Força/i)).toBeInTheDocument();
    expect(screen.getByText(/Distribuição por grupamento/i)).toBeInTheDocument();
  });

  it('should render radar chart container', () => {
    const { container } = render(<WidgetStrengthRadar data={mockData} />);
    expect(container.querySelector('svg')).toBeInTheDocument();
  });
});
