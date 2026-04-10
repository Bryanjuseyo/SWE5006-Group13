/**
 * Component tests — src/components/JobRequestList.tsx
 *
 * Tests cover: loading state, successful render of cards,
 * empty state message, end-user action buttons, error state.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import JobRequestList from './JobRequestList';
import * as jobRequestsApi from '../api/job_requests';
import * as storage from '../auth/storage';

vi.mock('../api/job_requests', () => ({
  getJobRequests: vi.fn(),
  deleteJobRequest: vi.fn(),
  updateJobStatus: vi.fn(),
}));

vi.mock('../auth/storage', () => ({
  getToken: vi.fn().mockReturnValue('test-token'),
  getUser: vi.fn(),
}));

const MOCK_END_USER = {
  id: 1,
  email: 'user@test.com',
  role: 'end_user' as const,
  created_at: '',
};

const MOCK_JOB: jobRequestsApi.JobRequest = {
  id: 42,
  title: 'Kitchen Deep Clean',
  description: 'Full clean of kitchen appliances.',
  service_type: 'full',
  location: '10 Orchard Road',
  status: 'pending',
  preferred_date: '2099-08-01',
  preferred_time_start: '09:00:00',
  preferred_time_end: '13:00:00',
  end_user_id: 1,
  cleaner_id: null,
  cleaner: null,
  end_user: null,
  is_in_priority_window: false,
  priority_window_end: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const MOCK_PAGINATION = { page: 1, per_page: 10, total: 0, total_pages: 0, has_prev: false, has_next: false };

describe('JobRequestList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows a loading spinner while the fetch is in-flight', () => {
    vi.mocked(storage.getUser).mockReturnValue(MOCK_END_USER);
    // Promise that never settles — component stays in loading state
    vi.mocked(jobRequestsApi.getJobRequests).mockReturnValue(new Promise(() => {}));

    render(<MemoryRouter><JobRequestList /></MemoryRouter>);

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders a job card for each returned job request', async () => {
    vi.mocked(storage.getUser).mockReturnValue(MOCK_END_USER);
    vi.mocked(jobRequestsApi.getJobRequests).mockResolvedValue({
      job_requests: [MOCK_JOB], pagination: MOCK_PAGINATION,
    });

    render(<MemoryRouter><JobRequestList /></MemoryRouter>);

    await waitFor(() => {
      expect(screen.getByText('Kitchen Deep Clean')).toBeInTheDocument();
    });
    expect(screen.getByText('#42')).toBeInTheDocument();
  });

  it('shows empty state message when there are no job requests', async () => {
    vi.mocked(storage.getUser).mockReturnValue(MOCK_END_USER);
    vi.mocked(jobRequestsApi.getJobRequests).mockResolvedValue({ job_requests: [], pagination: MOCK_PAGINATION });

    render(<MemoryRouter><JobRequestList /></MemoryRouter>);

    await waitFor(() => {
      expect(screen.getByText(/no job requests found/i)).toBeInTheDocument();
    });
  });

  it('shows the New Job Request button for end_user role', async () => {
    vi.mocked(storage.getUser).mockReturnValue(MOCK_END_USER);
    vi.mocked(jobRequestsApi.getJobRequests).mockResolvedValue({ job_requests: [], pagination: MOCK_PAGINATION });

    render(<MemoryRouter><JobRequestList /></MemoryRouter>);

    await waitFor(() => {
      expect(screen.getByText(/\+ new job request/i)).toBeInTheDocument();
    });
  });

  it('displays an error alert when the fetch fails', async () => {
    vi.mocked(storage.getUser).mockReturnValue(MOCK_END_USER);
    vi.mocked(jobRequestsApi.getJobRequests).mockRejectedValue(
      new Error('Failed to load job requests.')
    );

    render(<MemoryRouter><JobRequestList /></MemoryRouter>);

    await waitFor(() => {
      expect(screen.getByText('Failed to load job requests.')).toBeInTheDocument();
    });
  });
});
