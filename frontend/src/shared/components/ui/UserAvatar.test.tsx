import { describe, it, expect } from 'vitest';

import { render, screen } from '../../utils/test-utils';

import { UserAvatar } from './UserAvatar';

describe('UserAvatar', () => {
  it('should render image if photo is provided', () => {
    render(<UserAvatar photo="https://example.com/photo.jpg" />);
    const img = screen.getByAltText('User avatar');
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('src', 'https://example.com/photo.jpg');
  });

  it('should render initial if no photo is provided', () => {
    render(<UserAvatar name="John Doe" />);
    expect(screen.getByText('J')).toBeInTheDocument();
  });

  it('should render ? if no photo and no name are provided', () => {
    render(<UserAvatar />);
    expect(screen.getByText('?')).toBeInTheDocument();
  });
});
