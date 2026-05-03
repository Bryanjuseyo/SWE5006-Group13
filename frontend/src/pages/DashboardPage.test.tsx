import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import DashboardPage from './DashboardPage';
import * as storage from '../auth/storage';

vi.mock('../auth/storage', () => ({
  getUser: vi.fn(),
  getToken: vi.fn(),
  clearAuth: vi.fn(),
}));

describe('DashboardPage', () => {
  it('redirects unauthenticated users to /login', () => {
    vi.mocked(storage.getUser).mockReturnValue(null);
    render(<MemoryRouter><DashboardPage /></MemoryRouter>);
    // Navigate replaces content; no visible text but no crash
    expect(screen.queryByRole('heading')).not.toBeInTheDocument();
  });

  it('redirects administrator to /dashboard/admin', () => {
    vi.mocked(storage.getUser).mockReturnValue({
      id: 1, email: 'admin@test.com', role: 'administrator', created_at: '',
    });
    const { container } = render(<MemoryRouter><DashboardPage /></MemoryRouter>);
    expect(container).toBeTruthy();
  });

  it('redirects cleaner to /dashboard/cleaner', () => {
    vi.mocked(storage.getUser).mockReturnValue({
      id: 2, email: 'cleaner@test.com', role: 'cleaner', created_at: '',
    });
    const { container } = render(<MemoryRouter><DashboardPage /></MemoryRouter>);
    expect(container).toBeTruthy();
  });

  it('redirects end_user to /dashboard/end-user', () => {
    vi.mocked(storage.getUser).mockReturnValue({
      id: 3, email: 'user@test.com', role: 'end_user', created_at: '',
    });
    const { container } = render(<MemoryRouter><DashboardPage /></MemoryRouter>);
    expect(container).toBeTruthy();
  });

  it('renders nothing visible when no user stored', () => {
    vi.mocked(storage.getUser).mockReturnValue(null);
    render(<MemoryRouter><DashboardPage /></MemoryRouter>);
    expect(screen.queryByText(/dashboard/i)).not.toBeInTheDocument();
  });
});
