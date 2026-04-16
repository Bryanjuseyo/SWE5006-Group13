import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import ForbiddenPage from './ForbiddenPage';

vi.mock('../auth/storage', () => ({
  getUser: vi.fn().mockReturnValue(null),
  clearAuth: vi.fn(),
}));

describe('ForbiddenPage', () => {
  it('renders the 403 heading', () => {
    render(<MemoryRouter><ForbiddenPage /></MemoryRouter>);
    expect(screen.getByText('403 Forbidden')).toBeInTheDocument();
  });

  it('renders the permission denied message', () => {
    render(<MemoryRouter><ForbiddenPage /></MemoryRouter>);
    // Use regex to avoid smart-quote vs ASCII-apostrophe mismatch in source
    expect(screen.getByText(/permission to access this page/i)).toBeInTheDocument();
  });

  it('renders a link to the dashboard', () => {
    render(<MemoryRouter><ForbiddenPage /></MemoryRouter>);
    const link = screen.getByRole('link', { name: /go to dashboard/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/dashboard');
  });

  it('renders without crashing', () => {
    const { container } = render(<MemoryRouter><ForbiddenPage /></MemoryRouter>);
    expect(container).toBeTruthy();
  });

  it('contains a main element', () => {
    render(<MemoryRouter><ForbiddenPage /></MemoryRouter>);
    expect(document.querySelector('main')).toBeInTheDocument();
  });
});
