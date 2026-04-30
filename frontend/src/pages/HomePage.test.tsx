import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import HomePage from './HomePage';

vi.mock('../auth/storage', () => ({
  getUser: vi.fn().mockReturnValue(null),
  clearAuth: vi.fn(),
}));

vi.mock('../components/Logo', () => ({
  default: () => <div data-testid="logo" />,
}));

describe('HomePage', () => {
  it('renders the CleanMatch brand name', () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(screen.getByText('CleanMatch')).toBeInTheDocument();
  });

  it('renders a Register link pointing to /register', () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    // Navbar may also render Register/Login links; assert at least one correct href exists
    const links = screen.getAllByRole('link', { name: /register/i });
    expect(links.some(l => l.getAttribute('href') === '/register')).toBe(true);
  });

  it('renders a Login link pointing to /login', () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    const links = screen.getAllByRole('link', { name: /login/i });
    expect(links.some(l => l.getAttribute('href') === '/login')).toBe(true);
  });

  it('renders the tagline description', () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(screen.getByText(/find suitable cleaners/i)).toBeInTheDocument();
  });

  it('renders without crashing', () => {
    const { container } = render(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(container).toBeTruthy();
  });
});
