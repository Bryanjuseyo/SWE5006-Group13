import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import AdminBookingsPage from './AdminBookingsPage';
import * as adminApi from '../api/admin';
import type { JobRequest } from '../api/job_requests';

vi.mock('../api/admin', () => ({
  getAdminBookings: vi.fn(),
  rejectBooking: vi.fn(),
}));

vi.mock('../auth/storage', () => ({
  getToken: vi.fn().mockReturnValue('admin-token'),
  getUser: vi.fn().mockReturnValue({ id: 1, email: 'admin@test.com', role: 'administrator', created_at: '' }),
  clearAuth: vi.fn(),
}));

const MOCK_BOOKING: JobRequest = {
  id: 7,
  title: 'Weekly Cleaning',
  description: '',
  service_type: 'partial',
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

const MOCK_PAGINATION = { page: 1, per_page: 10, total: 0, total_pages: 0, has_prev: false, has_next: false };

describe('AdminBookingsPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('shows loading spinner while fetching', () => {
    vi.mocked(adminApi.getAdminBookings).mockReturnValue(new Promise(() => {}));
    render(<MemoryRouter><AdminBookingsPage /></MemoryRouter>);
    expect(document.querySelector('.spinner-border')).toBeInTheDocument();
  });

  it('renders the page heading', async () => {
    vi.mocked(adminApi.getAdminBookings).mockResolvedValue({ job_requests: [], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminBookingsPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Manage Bookings')).toBeInTheDocument();
    });
  });

  it('renders booking rows in the table', async () => {
    vi.mocked(adminApi.getAdminBookings).mockResolvedValue({ job_requests: [MOCK_BOOKING], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminBookingsPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Weekly Cleaning')).toBeInTheDocument();
    });
  });

  it('shows empty state when no bookings found', async () => {
    vi.mocked(adminApi.getAdminBookings).mockResolvedValue({ job_requests: [], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminBookingsPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText(/no bookings found/i)).toBeInTheDocument();
    });
  });

  it('shows error alert when fetch fails', async () => {
    vi.mocked(adminApi.getAdminBookings).mockRejectedValue(new Error('Failed to load bookings.'));
    render(<MemoryRouter><AdminBookingsPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Failed to load bookings.')).toBeInTheDocument();
    });
  });

  it('renders a View link for each booking', async () => {
    vi.mocked(adminApi.getAdminBookings).mockResolvedValue({ job_requests: [MOCK_BOOKING], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminBookingsPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('link', { name: /view/i })).toBeInTheDocument();
    });
  });

  it('renders a Reject button for active bookings', async () => {
    vi.mocked(adminApi.getAdminBookings).mockResolvedValue({ job_requests: [MOCK_BOOKING], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminBookingsPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument();
    });
  });

  it('submitting the search form triggers a new fetch', async () => {
    vi.mocked(adminApi.getAdminBookings).mockResolvedValue({ job_requests: [], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><AdminBookingsPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /search/i }));

    await userEvent.type(screen.getByPlaceholderText(/search by title/i), 'office');
    await userEvent.click(screen.getByRole('button', { name: /search/i }));

    await waitFor(() => {
      expect(adminApi.getAdminBookings).toHaveBeenCalledTimes(2);
    });
  });

  it('shows pagination controls when has_next is true', async () => {
    const pagedPagination = { page: 1, per_page: 25, total: 30, total_pages: 2, has_prev: false, has_next: true };
    vi.mocked(adminApi.getAdminBookings).mockResolvedValue({ job_requests: [MOCK_BOOKING], pagination: pagedPagination });
    render(<MemoryRouter><AdminBookingsPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /next/i }));

    expect(screen.getByRole('button', { name: /next/i })).not.toBeDisabled();
  });
});

describe('AdminBookingsPage – reject', () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.restoreAllMocks());

  it('clicking Reject with confirmation calls rejectBooking', async () => {
    vi.mocked(adminApi.getAdminBookings).mockResolvedValue({ job_requests: [MOCK_BOOKING], pagination: MOCK_PAGINATION });
    vi.mocked(adminApi.rejectBooking).mockResolvedValue({
      message: 'Rejected.',
      job_request: { ...MOCK_BOOKING, status: 'rejected' as const },
    });
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    render(<MemoryRouter><AdminBookingsPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /reject/i }));

    await userEvent.click(screen.getByRole('button', { name: /reject/i }));

    await waitFor(() => {
      expect(adminApi.rejectBooking).toHaveBeenCalledWith(MOCK_BOOKING.id, 'admin-token');
    });
  });
});
