import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import BrowseJobsPage from './BrowseJobsPage';
import * as jobRequestsApi from '../api/job_requests';
import * as storage from '../auth/storage';

vi.mock('../api/job_requests', () => ({
  getAvailableJobs: vi.fn(),
  updateJobStatus: vi.fn(),
}));

vi.mock('../auth/storage', () => ({
  getToken: vi.fn().mockReturnValue('test-token'),
  getUser: vi.fn(),
  clearAuth: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

const MOCK_JOB: jobRequestsApi.JobRequest = {
  id: 10,
  title: 'Office Deep Clean',
  description: 'Clean the entire office.',
  service_type: 'full',
  location: '5 Raffles Place',
  status: 'pending',
  preferred_date: '2099-09-01',
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

describe('BrowseJobsPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('shows a loading spinner while fetching', () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'c@test.com', role: 'cleaner', created_at: '' });
    vi.mocked(jobRequestsApi.getAvailableJobs).mockReturnValue(new Promise(() => {}));
    render(<MemoryRouter><BrowseJobsPage /></MemoryRouter>);
    expect(document.querySelector('.spinner-border')).toBeInTheDocument();
  });

  it('renders job cards after fetch', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'c@test.com', role: 'cleaner', created_at: '' });
    vi.mocked(jobRequestsApi.getAvailableJobs).mockResolvedValue({ job_requests: [MOCK_JOB], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><BrowseJobsPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Office Deep Clean')).toBeInTheDocument();
    });
  });

  it('shows empty state when no jobs available', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'c@test.com', role: 'cleaner', created_at: '' });
    vi.mocked(jobRequestsApi.getAvailableJobs).mockResolvedValue({ job_requests: [], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><BrowseJobsPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText(/no available jobs/i)).toBeInTheDocument();
    });
  });

  it('shows an error when fetch fails', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'c@test.com', role: 'cleaner', created_at: '' });
    vi.mocked(jobRequestsApi.getAvailableJobs).mockRejectedValue(new Error('Failed to load available jobs.'));
    render(<MemoryRouter><BrowseJobsPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Failed to load available jobs.')).toBeInTheDocument();
    });
  });

  it('renders the page heading', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'c@test.com', role: 'cleaner', created_at: '' });
    vi.mocked(jobRequestsApi.getAvailableJobs).mockResolvedValue({ job_requests: [], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><BrowseJobsPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Available Jobs')).toBeInTheDocument();
    });
  });

  it('clicking Accept Job calls updateJobStatus and navigates to /cleaner/schedule', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'c@test.com', role: 'cleaner', created_at: '' });
    vi.mocked(jobRequestsApi.getAvailableJobs).mockResolvedValue({ job_requests: [MOCK_JOB], pagination: MOCK_PAGINATION });
    vi.mocked(jobRequestsApi.updateJobStatus).mockResolvedValue({
      message: 'ok',
      job_request: { ...MOCK_JOB, status: 'confirmed' as const },
    });
    render(<MemoryRouter><BrowseJobsPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /accept job/i }));

    await userEvent.click(screen.getByRole('button', { name: /accept job/i }));

    await waitFor(() => {
      expect(jobRequestsApi.updateJobStatus).toHaveBeenCalledWith(MOCK_JOB.id, 'confirmed', 'test-token');
      expect(mockNavigate).toHaveBeenCalledWith('/cleaner/schedule');
    });
  });

  it('renders job location in the card', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'c@test.com', role: 'cleaner', created_at: '' });
    vi.mocked(jobRequestsApi.getAvailableJobs).mockResolvedValue({ job_requests: [MOCK_JOB], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><BrowseJobsPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('5 Raffles Place')).toBeInTheDocument();
    });
  });

  it('shows Next button enabled and Previous button disabled on first page when has_next', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'c@test.com', role: 'cleaner', created_at: '' });
    const pagedPagination = { page: 1, per_page: 25, total: 30, total_pages: 2, has_prev: false, has_next: true };
    vi.mocked(jobRequestsApi.getAvailableJobs).mockResolvedValue({ job_requests: [MOCK_JOB], pagination: pagedPagination });
    render(<MemoryRouter><BrowseJobsPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /next/i }));

    expect(screen.getByRole('button', { name: /next/i })).not.toBeDisabled();
    expect(screen.getByRole('button', { name: /previous/i })).toBeDisabled();
  });

  it('shows Preferred badge when job cleaner_id matches the current user', async () => {
    const preferredJob = { ...MOCK_JOB, cleaner_id: 2 };
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'c@test.com', role: 'cleaner', created_at: '' });
    vi.mocked(jobRequestsApi.getAvailableJobs).mockResolvedValue({ job_requests: [preferredJob], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><BrowseJobsPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Preferred')).toBeInTheDocument();
    });
  });
});
