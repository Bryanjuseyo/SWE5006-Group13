import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
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

  it('renders Ban button for non-administrator user', async () => {
    vi.mocked(adminApi.getAdminUsers).mockResolvedValue({ users: [MOCK_USER], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminUsersPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /^ban$/i })).toBeInTheDocument();
    });
  });

  it('clicking Ban button shows inline input and Confirm button', async () => {
    vi.mocked(adminApi.getAdminUsers).mockResolvedValue({ users: [MOCK_USER], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminUsersPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /^ban$/i }));

    await userEvent.click(screen.getByRole('button', { name: /^ban$/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /confirm/i })).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/reason/i)).toBeInTheDocument();
    });
  });

  it('clicking Cancel in ban flow hides the ban input', async () => {
    vi.mocked(adminApi.getAdminUsers).mockResolvedValue({ users: [MOCK_USER], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminUsersPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /^ban$/i }));

    await userEvent.click(screen.getByRole('button', { name: /^ban$/i }));
    await waitFor(() => screen.getByRole('button', { name: /cancel/i }));

    await userEvent.click(screen.getByRole('button', { name: /cancel/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /^ban$/i })).toBeInTheDocument();
    });
  });

  it('submitting ban form calls banUser', async () => {
    const bannedUser: adminApi.AdminUser = { ...MOCK_USER, is_banned: true };
    vi.mocked(adminApi.getAdminUsers).mockResolvedValue({ users: [MOCK_USER], pagination: MOCK_PAGINATION });
    vi.mocked(adminApi.banUser).mockResolvedValue({ message: 'Banned.', user: bannedUser });
    render(<MemoryRouter><AdminUsersPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /^ban$/i }));

    await userEvent.click(screen.getByRole('button', { name: /^ban$/i }));
    await waitFor(() => screen.getByRole('button', { name: /confirm/i }));
    await userEvent.click(screen.getByRole('button', { name: /confirm/i }));

    await waitFor(() => {
      expect(adminApi.banUser).toHaveBeenCalledWith(MOCK_USER.id, 'admin-token', undefined);
    });
  });

  it('renders Unban button for banned user', async () => {
    const bannedUser: adminApi.AdminUser = { ...MOCK_USER, is_banned: true, ban_reason: 'Spam' };
    vi.mocked(adminApi.getAdminUsers).mockResolvedValue({ users: [bannedUser], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminUsersPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /unban/i })).toBeInTheDocument();
    });
  });

  it('submitting search form triggers a new fetch', async () => {
    vi.mocked(adminApi.getAdminUsers).mockResolvedValue({ users: [], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminUsersPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /search/i }));

    await userEvent.type(screen.getByPlaceholderText(/search by email/i), 'alice');
    await userEvent.click(screen.getByRole('button', { name: /search/i }));

    await waitFor(() => {
      expect(adminApi.getAdminUsers).toHaveBeenCalledTimes(2);
    });
  });

  it('shows pagination controls when has_next is true', async () => {
    const pagedPagination = { page: 1, per_page: 25, total: 30, total_pages: 2, has_prev: false, has_next: true };
    vi.mocked(adminApi.getAdminUsers).mockResolvedValue({ users: [MOCK_USER], pagination: pagedPagination });
    render(<MemoryRouter><AdminUsersPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /next/i }));

    expect(screen.getByRole('button', { name: /next/i })).not.toBeDisabled();
    expect(screen.getByRole('button', { name: /previous/i })).toBeDisabled();
  });
});

describe('AdminUsersPage – unban', () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.restoreAllMocks());

  it('clicking Unban with confirmation calls unbanUser', async () => {
    const bannedUser: adminApi.AdminUser = { ...MOCK_USER, is_banned: true };
    const unbannedUser: adminApi.AdminUser = { ...MOCK_USER, is_banned: false };
    vi.mocked(adminApi.getAdminUsers).mockResolvedValue({ users: [bannedUser], pagination: MOCK_PAGINATION });
    vi.mocked(adminApi.unbanUser).mockResolvedValue({ message: 'Unbanned.', user: unbannedUser });
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    render(<MemoryRouter><AdminUsersPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /unban/i }));

    await userEvent.click(screen.getByRole('button', { name: /unban/i }));

    await waitFor(() => {
      expect(adminApi.unbanUser).toHaveBeenCalledWith(bannedUser.id, 'admin-token');
    });
  });
});
