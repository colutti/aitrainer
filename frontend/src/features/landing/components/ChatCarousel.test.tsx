import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { ChatCarousel } from './ChatCarousel';

describe('ChatCarousel Component', () => {
  it('should render chat conversations', () => {
    render(<ChatCarousel />);
    expect(screen.getByText(/Experimente agora/i)).toBeInTheDocument();
  });
});
