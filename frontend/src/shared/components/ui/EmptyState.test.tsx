import { FolderOpen } from 'lucide-react';
import { describe, it, expect, vi } from 'vitest';

import { render, screen, fireEvent } from '../../utils/test-utils';

import { EmptyState } from './EmptyState';

describe('EmptyState', () => {
  it('should render title and description', () => {
    render(<EmptyState title="No data" description="Try again later" icon={FolderOpen} />);
    expect(screen.getByText('No data')).toBeInTheDocument();
    expect(screen.getByText('Try again later')).toBeInTheDocument();
  });

  it('should call onAction when button clicked', () => {
    const onAction = vi.fn();
    render(
      <EmptyState 
        title="No data" 
        description="Try again later" 
        icon={FolderOpen} 
        actionLabel="Retry" 
        onAction={onAction} 
      />
    );
    
    const btn = screen.getByText('Retry');
    fireEvent.click(btn);
    expect(onAction).toHaveBeenCalled();
  });
});
