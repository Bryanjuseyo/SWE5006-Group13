/**
 * Hook / guard tests — src/auth/guards.tsx
 *
 * RequireAuth and RequireRole act as route guards that read auth state
 * (via getUser) and either render their children or redirect.
 *
 * Tests cover: authenticated access, unauthenticated redirect,
 * correct-role access, wrong-role redirect.
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RequireAuth, RequireRole } from './guards';
import * as storage from './storage';

vi.mock('./storage', () => ({
  getUser: vi.fn(),
}));

const MOCK_END_USER = {
  id: 1,
  email: 'user@test.com',
  role: 'end_user' as const,
  created_at: '2024-01-01T00:00:00Z',
};

describe('RequireAuth', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders children when a user is stored', () => {
    vi.mocked(storage.getUser).mockReturnValue(MOCK_END_USER);

    render(
      <MemoryRouter>
        <RequireAuth><div>Protected Content</div></RequireAuth>
      </MemoryRouter>
    );

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('does not render children and redirects when no user is stored', () => {
    vi.mocked(storage.getUser).mockReturnValue(null);

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <RequireAuth><div>Protected Content</div></RequireAuth>
      </MemoryRouter>
    );

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });
});

describe('RequireRole', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders children when the user has the required role', () => {
    vi.mocked(storage.getUser).mockReturnValue(MOCK_END_USER);

    render(
      <MemoryRouter>
        <RequireRole role="end_user"><div>Role Content</div></RequireRole>
      </MemoryRouter>
    );

    expect(screen.getByText('Role Content')).toBeInTheDocument();
  });

  it('does not render children when the user has a different role', () => {
    vi.mocked(storage.getUser).mockReturnValue({ ...MOCK_END_USER, role: 'cleaner' });

    render(
      <MemoryRouter>
        <RequireRole role="end_user"><div>Role Content</div></RequireRole>
      </MemoryRouter>
    );

    expect(screen.queryByText('Role Content')).not.toBeInTheDocument();
  });

  it('does not render children and redirects to login when no user is stored', () => {
    vi.mocked(storage.getUser).mockReturnValue(null);

    render(
      <MemoryRouter>
        <RequireRole role="administrator"><div>Admin Content</div></RequireRole>
      </MemoryRouter>
    );

    expect(screen.queryByText('Admin Content')).not.toBeInTheDocument();
  });
});
