import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
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

  it('shows Start Job and Cancel buttons for cleaner with confirmed job', async () => {
    const confirmedJob = { ...MOCK_JOB, status: 'confirmed' as const, cleaner_id: 2 };
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'cleaner@test.com', role: 'cleaner', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: confirmedJob });
    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start job/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^cancel$/i })).toBeInTheDocument();
    });
  });

  it('shows Mark as Completed button for cleaner with in_progress job', async () => {
    const inProgressJob = { ...MOCK_JOB, status: 'in_progress' as const, cleaner_id: 2 };
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'cleaner@test.com', role: 'cleaner', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: inProgressJob });
    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /mark as completed/i })).toBeInTheDocument();
    });
  });

  it('shows Confirm Completion button for end_user with cleaner_completed job', async () => {
    const cleanerCompletedJob = { ...MOCK_JOB, status: 'cleaner_completed' as const, cleaner_id: 2 };
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: cleanerCompletedJob });
    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /confirm completion/i })).toBeInTheDocument();
    });
  });

  it('shows Cancel Request button for end_user with cleaner-assigned pending job', async () => {
    const assignedJob = { ...MOCK_JOB, status: 'pending' as const, cleaner_id: 2 };
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: assignedJob });
    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /cancel request/i })).toBeInTheDocument();
    });
  });

  it('shows "Open to all cleaners" badge for pending job with no cleaner assigned', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: MOCK_JOB });
    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Open to all cleaners')).toBeInTheDocument();
    });
  });

  it('renders job description when present', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: MOCK_JOB });
    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Deep clean of the apartment.')).toBeInTheDocument();
    });
  });

  it('shows admin-specific breadcrumb for administrator role', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 3, email: 'admin@test.com', role: 'administrator', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: MOCK_JOB });
    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    await waitFor(() => {
      const links = screen.getAllByRole('link', { name: /manage bookings/i });
      expect(links.length).toBeGreaterThan(0);
    });
  });
});

describe('JobRequestDetailPage – actions', () => {
  afterEach(() => vi.restoreAllMocks());
  beforeEach(() => vi.clearAllMocks());

  it('calls deleteJobRequest and navigates when Delete is confirmed', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: MOCK_JOB });
    vi.mocked(jobRequestsApi.deleteJobRequest).mockResolvedValue({ message: 'Deleted.' });
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /delete/i }));

    await userEvent.click(screen.getByRole('button', { name: /delete/i }));

    await waitFor(() => {
      expect(jobRequestsApi.deleteJobRequest).toHaveBeenCalledWith(42, 'test-token');
      expect(mockNavigate).toHaveBeenCalledWith('/job-requests', { replace: true });
    });
  });

  it('does not call deleteJobRequest when Delete confirmation is cancelled', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: MOCK_JOB });
    vi.spyOn(window, 'confirm').mockReturnValue(false);

    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /delete/i }));

    await userEvent.click(screen.getByRole('button', { name: /delete/i }));

    await waitFor(() => {
      expect(jobRequestsApi.deleteJobRequest).not.toHaveBeenCalled();
    });
  });

  it('clicking Accept Job calls updateJobStatus with confirmed', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'cleaner@test.com', role: 'cleaner', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: MOCK_JOB });
    vi.mocked(jobRequestsApi.updateJobStatus).mockResolvedValue({
      message: 'ok',
      job_request: { ...MOCK_JOB, status: 'confirmed' as const, cleaner_id: 2 },
    });
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /accept job/i }));

    await userEvent.click(screen.getByRole('button', { name: /accept job/i }));

    await waitFor(() => {
      expect(jobRequestsApi.updateJobStatus).toHaveBeenCalledWith(42, 'confirmed', 'test-token');
    });
  });

  it('clicking Start Job calls updateJobStatus with in_progress', async () => {
    const confirmedJob = { ...MOCK_JOB, status: 'confirmed' as const, cleaner_id: 2 };
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'cleaner@test.com', role: 'cleaner', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: confirmedJob });
    vi.mocked(jobRequestsApi.updateJobStatus).mockResolvedValue({
      message: 'ok',
      job_request: { ...confirmedJob, status: 'in_progress' as const },
    });
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /start job/i }));

    await userEvent.click(screen.getByRole('button', { name: /start job/i }));

    await waitFor(() => {
      expect(jobRequestsApi.updateJobStatus).toHaveBeenCalledWith(42, 'in_progress', 'test-token');
    });
  });

  it('clicking Mark as Completed calls updateJobStatus with cleaner_completed', async () => {
    const inProgressJob = { ...MOCK_JOB, status: 'in_progress' as const, cleaner_id: 2 };
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'cleaner@test.com', role: 'cleaner', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: inProgressJob });
    vi.mocked(jobRequestsApi.updateJobStatus).mockResolvedValue({
      message: 'ok',
      job_request: { ...inProgressJob, status: 'cleaner_completed' as const },
    });
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /mark as completed/i }));

    await userEvent.click(screen.getByRole('button', { name: /mark as completed/i }));

    await waitFor(() => {
      expect(jobRequestsApi.updateJobStatus).toHaveBeenCalledWith(42, 'cleaner_completed', 'test-token');
    });
  });

  it('clicking Confirm Completion calls updateJobStatus with completed', async () => {
    const cleanerCompletedJob = { ...MOCK_JOB, status: 'cleaner_completed' as const, cleaner_id: 2 };
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: cleanerCompletedJob });
    vi.mocked(jobRequestsApi.updateJobStatus).mockResolvedValue({
      message: 'ok',
      job_request: { ...cleanerCompletedJob, status: 'completed' as const },
    });
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<MemoryRouter><JobRequestDetailPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /confirm completion/i }));

    await userEvent.click(screen.getByRole('button', { name: /confirm completion/i }));

    await waitFor(() => {
      expect(jobRequestsApi.updateJobStatus).toHaveBeenCalledWith(42, 'completed', 'test-token');
    });
  });
});
