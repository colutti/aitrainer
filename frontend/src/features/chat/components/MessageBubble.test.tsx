import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { MessageBubble } from './MessageBubble';

describe('MessageBubble', () => {
  it('should render user message correctly', () => {
    const message = {
      id: '1',
      sender: 'Student' as const,
      text: 'Hello Trainer',
      timestamp: new Date().toISOString(),
    };

    render(<MessageBubble message={message} />);

    expect(screen.getByText('Hello Trainer')).toBeInTheDocument();
    // Check for user-specific class or structure if needed
    // The component uses 'flex-row-reverse' for user.
    // We can just verify content for now.
  });

  it('should render trainer message with markdown', () => {
    const message = {
      id: '2',
      sender: 'Trainer' as const,
      text: '**Bold Response**',
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={message} />);

    // ReactMarkdown should render strong tag
    expect(container.querySelector('strong')).toHaveTextContent('Bold Response');
  });

  it('should render loading dots when text is empty (streaming start)', () => {
     const message = {
      id: '3',
      sender: 'Trainer' as const,
      text: '',
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={message} />);
    // Look for generic dots structure
    expect(container.querySelectorAll('.animate-bounce')).toHaveLength(3);
  });

  it('should render trainer avatar when trainerId is provided', () => {
    const message = {
      id: '4',
      sender: 'Trainer' as const,
      text: 'Hello Student',
      timestamp: new Date().toISOString(),
    };

    render(<MessageBubble message={message} trainerId="marcus" />);
    
    const avatarImg = screen.getByAltText('Trainer');
    expect(avatarImg).toBeInTheDocument();
    expect(avatarImg).toHaveAttribute('src', '/assets/avatars/marcus.png');
  });
});
