import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import AdminDashboard from './AdminDashboard';
import * as adminApi from '../api/admin';
import type { JobRequest } from '../api/job_requests';

vi.mock('../api/admin', () => ({
  getAdminStats: vi.fn(),
  getAdminBookings: vi.fn(),
  rejectBooking: vi.fn(),
}));

vi.mock('../auth/storage', () => ({
  getToken: vi.fn().mockReturnValue('admin-token'),
  getUser: vi.fn().mockReturnValue({ id: 1, email: 'admin@test.com', role: 'administrator', created_at: '' }),
  clearAuth: vi.fn(),
}));

const MOCK_STATS: adminApi.DashboardStats = {
  users: { total: 10, end_users: 6, cleaners: 3, administrators: 1, banned: 0 },
  jobs: { total: 5, pending: 2, confirmed: 1, in_progress: 1, completed: 1, cancelled: 0, rejected: 0 },
};

const MOCK_PAGINATION = { page: 1, per_page: 10, total: 0, total_pages: 0, has_prev: false, has_next: false };

const MOCK_BOOKING: JobRequest = {
  id: 7,
  title: 'Office Clean',
  description: '',
  service_type: 'full',
  location: '1 Raffles Place',
  status: 'pending',
  preferred_date: '2099-08-15',
  preferred_time_start: null,
  preferred_time_end: null,
  end_user_id: 2,
  cleaner_id: null,
  cleaner: null,
  end_user: { id: 2, email: 'user@test.com', role: 'end_user', created_at: '' },
  is_in_priority_window: false,
  priority_window_end: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

describe('AdminDashboard', () => {
  beforeEach(() => vi.clearAllMocks());

  it('shows loading spinner while fetching', () => {
    vi.mocked(adminApi.getAdminStats).mockReturnValue(new Promise(() => {}));
    vi.mocked(adminApi.getAdminBookings).mockReturnValue(new Promise(() => {}));
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);
    expect(document.querySelector('.spinner-border')).toBeInTheDocument();
  });

  it('renders the Admin Dashboard heading', async () => {
    vi.mocked(adminApi.getAdminStats).mockResolvedValue(MOCK_STATS);
    vi.mocked(adminApi.getAdminBookings).mockResolvedValue({ job_requests: [], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
    });
  });

  it('renders stats cards with user counts', async () => {
    vi.mocked(adminApi.getAdminStats).mockResolvedValue(MOCK_STATS);
    vi.mocked(adminApi.getAdminBookings).mockResolvedValue({ job_requests: [], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Total Users')).toBeInTheDocument();
    });
  });

  it('shows error alert when fetch fails', async () => {
    vi.mocked(adminApi.getAdminStats).mockRejectedValue(new Error('Failed to load dashboard.'));
    vi.mocked(adminApi.getAdminBookings).mockRejectedValue(new Error('Failed to load dashboard.'));
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Failed to load dashboard.')).toBeInTheDocument();
    });
  });

  it('renders Manage Users and Manage Bookings nav cards', async () => {
    vi.mocked(adminApi.getAdminStats).mockResolvedValue(MOCK_STATS);
    vi.mocked(adminApi.getAdminBookings).mockResolvedValue({ job_requests: [], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Manage Users')).toBeInTheDocument();
      expect(screen.getByText('Manage Bookings')).toBeInTheDocument();
    });
  });

  it('renders recent booking rows when bookings are returned', async () => {
    vi.mocked(adminApi.getAdminStats).mockResolvedValue(MOCK_STATS);
    vi.mocked(adminApi.getAdminBookings).mockResolvedValue({ job_requests: [MOCK_BOOKING], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Office Clean')).toBeInTheDocument();
    });
  });
});

describe('AdminDashboard – reject', () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.restoreAllMocks());

  it('clicking Reject with confirmation calls rejectBooking', async () => {
    vi.mocked(adminApi.getAdminStats).mockResolvedValue(MOCK_STATS);
    vi.mocked(adminApi.getAdminBookings).mockResolvedValue({ job_requests: [MOCK_BOOKING], pagination: MOCK_PAGINATION });
    vi.mocked(adminApi.rejectBooking).mockResolvedValue({
      message: 'Rejected.',
      job_request: { ...MOCK_BOOKING, status: 'rejected' as const },
    });
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /reject/i }));

    await userEvent.click(screen.getByRole('button', { name: /reject/i }));

    await waitFor(() => {
      expect(adminApi.rejectBooking).toHaveBeenCalledWith(MOCK_BOOKING.id, 'admin-token');
    });
  });
});
