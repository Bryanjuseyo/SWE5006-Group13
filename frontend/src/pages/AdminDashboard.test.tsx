import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AdminDashboard from './AdminDashboard';
import * as adminApi from '../api/admin';

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
    vi.mocked(adminApi.getAdminBookings).mockResolvedValue({ job_requests: [] });
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
    });
  });

  it('renders stats cards with user counts', async () => {
    vi.mocked(adminApi.getAdminStats).mockResolvedValue(MOCK_STATS);
    vi.mocked(adminApi.getAdminBookings).mockResolvedValue({ job_requests: [] });
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
    vi.mocked(adminApi.getAdminBookings).mockResolvedValue({ job_requests: [] });
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Manage Users')).toBeInTheDocument();
      expect(screen.getByText('Manage Bookings')).toBeInTheDocument();
    });
  });
});
