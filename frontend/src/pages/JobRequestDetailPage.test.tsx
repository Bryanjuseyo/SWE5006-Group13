import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import JobRequestDetailPage from './JobRequestDetailPage';
import * as jobRequestsApi from '../api/job_requests';
import * as storage from '../auth/storage';

vi.mock('../api/job_requests', () => ({
  getJobRequest: vi.fn(),
  deleteJobRequest: vi.fn(),
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
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: '42' }),
  };
});

const MOCK_JOB: jobRequestsApi.JobRequest = {
  id: 42,
  title: 'Home Cleaning',
  description: 'Deep clean of the apartment.',
  service_type: 'full',
  location: '5 Orchard Road',
  status: 'pending',
  preferred_date: '2099-11-15',
  preferred_time_start: '10:00:00',
  preferred_time_end: '14:00:00',
  end_user_id: 1,
  cleaner_id: null,
  cleaner: null,
  end_user: { id: 1, email: 'user@test.com', role: 'end_user', created_at: '' },
  is_in_priority_window: false,
  priority_window_end: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

describe('JobRequestDetailPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('shows loading spinner while fetching', () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockReturnValue(new Promise(() => {}));
    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    expect(document.querySelector('.spinner-border')).toBeInTheDocument();
  });

  it('renders job title after fetch', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: MOCK_JOB });
    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Home Cleaning')).toBeInTheDocument();
    });
  });

  it('shows error alert when fetch fails', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockRejectedValue(
      new Error('Failed to load job request.')
    );
    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Failed to load job request.')).toBeInTheDocument();
    });
  });

  it('shows Edit and Delete buttons for end_user with pending job', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: MOCK_JOB });
    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('link', { name: /edit/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
    });
  });

  it('shows Accept Job and Decline buttons for cleaner with pending job', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'cleaner@test.com', role: 'cleaner', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: MOCK_JOB });
    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /accept job/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /decline/i })).toBeInTheDocument();
    });
  });
});
