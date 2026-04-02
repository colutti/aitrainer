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

  it('toggles tooltip content on click and closes on outside click', () => {
    render(
      <div>
        <HelpTooltip content="Upload help" />
        <button type="button">outside</button>
      </div>
    );

    const helpButton = screen.getByRole('button', { name: /ajuda/i });
    fireEvent.click(helpButton);
    expect(screen.getByText('Upload help')).toBeInTheDocument();

    fireEvent.mouseDown(screen.getByRole('button', { name: 'outside' }));
    expect(screen.queryByText('Upload help')).not.toBeInTheDocument();
  });
});
