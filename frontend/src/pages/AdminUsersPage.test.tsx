import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AdminUsersPage from './AdminUsersPage';
import * as adminApi from '../api/admin';

vi.mock('../api/admin', () => ({
  getAdminUsers: vi.fn(),
  banUser: vi.fn(),
  unbanUser: vi.fn(),
}));

vi.mock('../auth/storage', () => ({
  getToken: vi.fn().mockReturnValue('admin-token'),
  getUser: vi.fn().mockReturnValue({ id: 1, email: 'admin@test.com', role: 'administrator', created_at: '' }),
  clearAuth: vi.fn(),
}));

const MOCK_USER: adminApi.AdminUser = {
  id: 2,
  email: 'user@test.com',
  role: 'end_user',
  is_banned: false,
  banned_at: null,
  ban_reason: null,
  created_at: '2024-01-01T00:00:00Z',
  last_login_at: null,
  profile: null,
};

const MOCK_PAGINATION = { page: 1, per_page: 10, total: 0, total_pages: 0, has_prev: false, has_next: false };

describe('AdminUsersPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('shows loading spinner while fetching', () => {
    vi.mocked(adminApi.getAdminUsers).mockReturnValue(new Promise(() => {}));
    render(<MemoryRouter><AdminUsersPage /></MemoryRouter>);
    expect(document.querySelector('.spinner-border')).toBeInTheDocument();
  });

  it('renders the page heading', async () => {
    vi.mocked(adminApi.getAdminUsers).mockResolvedValue({ users: [], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminUsersPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Manage Users')).toBeInTheDocument();
    });
  });

  it('renders user rows after fetch', async () => {
    vi.mocked(adminApi.getAdminUsers).mockResolvedValue({ users: [MOCK_USER], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminUsersPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('user@test.com')).toBeInTheDocument();
    });
  });

  it('shows empty state when no users found', async () => {
    vi.mocked(adminApi.getAdminUsers).mockResolvedValue({ users: [], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminUsersPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText(/no users found/i)).toBeInTheDocument();
    });
  });

  it('shows error alert when fetch fails', async () => {
    vi.mocked(adminApi.getAdminUsers).mockRejectedValue(new Error('Failed to load users.'));
    render(<MemoryRouter><AdminUsersPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Failed to load users.')).toBeInTheDocument();
    });
  });
});
