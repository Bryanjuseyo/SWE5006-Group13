import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Logo from './Logo';

describe('Logo', () => {
  it('renders the logo image with alt text', () => {
    render(<Logo />);
    expect(screen.getByAltText('CleanMatch')).toBeInTheDocument();
  });

  it('renders CleanMatch text label in small (default) size', () => {
    render(<Logo />);
    expect(screen.getByText('CleanMatch')).toBeInTheDocument();
  });

  it('renders image with height 32 in small size', () => {
    render(<Logo size="sm" />);
    const img = screen.getByAltText('CleanMatch');
    expect(img).toHaveAttribute('height', '32');
  });

  it('renders image with height 140 in large size', () => {
    render(<Logo size="lg" />);
    const img = screen.getByAltText('CleanMatch');
    expect(img).toHaveAttribute('height', '140');
  });

  it('does not render text label in large size', () => {
    render(<Logo size="lg" />);
    expect(screen.queryByText('CleanMatch')).not.toBeInTheDocument();
  });
});
