import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ViewHeader } from './ViewHeader';

describe('ViewHeader', () => {
  it('renders title before subtitle in the DOM flow', () => {
    render(<ViewHeader title="Meus Treinos" subtitle="Gerencie seu histórico de performance" />);

    const title = screen.getByTestId('view-header-title');
    const subtitle = screen.getByTestId('view-header-subtitle');

    expect(title.compareDocumentPosition(subtitle) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});
