import { render, screen, waitFor } from '@testing-library/react';
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
    vi.mocked(jobRequestsApi.getAvailableJobs).mockResolvedValue({ job_requests: [MOCK_JOB] });
    render(<MemoryRouter><BrowseJobsPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Office Deep Clean')).toBeInTheDocument();
    });
  });

  it('shows empty state when no jobs available', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'c@test.com', role: 'cleaner', created_at: '' });
    vi.mocked(jobRequestsApi.getAvailableJobs).mockResolvedValue({ job_requests: [] });
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
    vi.mocked(jobRequestsApi.getAvailableJobs).mockResolvedValue({ job_requests: [] });
    render(<MemoryRouter><BrowseJobsPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Available Jobs')).toBeInTheDocument();
    });
  });
});
