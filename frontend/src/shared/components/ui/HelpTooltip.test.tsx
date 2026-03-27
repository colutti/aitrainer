import { fireEvent, render, screen } from '../../utils/test-utils';

import { HelpTooltip } from './HelpTooltip';

describe('HelpTooltip', () => {
  it('shows and hides tooltip content on hover', () => {
    render(<HelpTooltip content="Protein target help" />);
    const button = screen.getByRole('button');

    fireEvent.mouseEnter(button);
    expect(screen.getByText('Protein target help')).toBeInTheDocument();

    fireEvent.mouseLeave(button);
    expect(screen.queryByText('Protein target help')).not.toBeInTheDocument();
  });
});
