import { render, screen } from '@testing-library/react';

import { DataList } from './DataList';

describe('DataList', () => {
  const mockData = [
    { id: '1', name: 'Item 1' },
    { id: '2', name: 'Item 2' },
  ];

  const defaultProps = {
    data: mockData,
    renderItem: (item: { id: string; name: string }) => <div data-testid="item">{item.name}</div>,
    keyExtractor: (item: { id: string }) => item.id,
    emptyState: {
      title: 'No Items',
      description: 'Add some items',
    },
  };

  it('renders list of items', () => {
    render(<DataList {...defaultProps} />);
    
    expect(screen.getAllByTestId('item')).toHaveLength(2);
    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Item 2')).toBeInTheDocument();
  });

  it('renders title and description', () => {
    render(<DataList {...defaultProps} title="My List" description="List Description" />);
    
    expect(screen.getByText('My List')).toBeInTheDocument();
    expect(screen.getByText('List Description')).toBeInTheDocument();
  });

  it('renders empty state when data is empty', () => {
    render(<DataList {...defaultProps} data={[]} />);
    
    expect(screen.getByText('No Items')).toBeInTheDocument();
    expect(screen.getByText('Add some items')).toBeInTheDocument();
  });

  it('renders loading state', () => {
    // Assuming loading state renders placeholders/skeletons, just checking essential parts don't crash
    // and empty state is NOT shown
    render(<DataList {...defaultProps} data={[]} isLoading={true} />);
    
    expect(screen.queryByText('No Items')).not.toBeInTheDocument();
  });
  
  it('renders actions', () => {
    render(<DataList {...defaultProps} actions={<button>Action</button>} />);
    expect(screen.getByText('Action')).toBeInTheDocument();
  });
  
  it('renders headerContent', () => {
      render(<DataList {...defaultProps} headerContent={<div data-testid="filter">Filter</div>} />);
      expect(screen.getByTestId('filter')).toBeInTheDocument();
  });
});
