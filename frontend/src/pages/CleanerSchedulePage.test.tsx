import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import CleanerSchedulePage from './CleanerSchedulePage';
import * as jobRequestsApi from '../api/job_requests';

vi.mock('../api/job_requests', () => ({
  getCleanerSchedule: vi.fn(),
  updateJobStatus: vi.fn(),
}));

vi.mock('../auth/storage', () => ({
  getToken: vi.fn().mockReturnValue('test-token'),
  getUser: vi.fn().mockReturnValue({ id: 2, email: 'cleaner@test.com', role: 'cleaner', created_at: '' }),
  clearAuth: vi.fn(),
}));

const MOCK_JOB: jobRequestsApi.JobRequest = {
  id: 5,
  title: 'Morning Clean',
  description: 'Clean the house.',
  service_type: 'partial',
  location: '20 Orchard Blvd',
  status: 'confirmed',
  preferred_date: '2099-10-01',
  preferred_time_start: '08:00:00',
  preferred_time_end: '12:00:00',
  end_user_id: 1,
  cleaner_id: 2,
  cleaner: null,
  end_user: { id: 1, email: 'user@test.com', role: 'end_user', created_at: '' },
  is_in_priority_window: false,
  priority_window_end: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const MOCK_PAGINATION = { page: 1, per_page: 10, total: 0, total_pages: 0, has_prev: false, has_next: false };

describe('CleanerSchedulePage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('shows loading spinner while fetching', () => {
    vi.mocked(jobRequestsApi.getCleanerSchedule).mockReturnValue(new Promise(() => {}));
    render(<MemoryRouter><CleanerSchedulePage /></MemoryRouter>);
    expect(document.querySelector('.spinner-border')).toBeInTheDocument();
  });

  it('renders job cards after fetch', async () => {
    vi.mocked(jobRequestsApi.getCleanerSchedule).mockResolvedValue({ schedule: [MOCK_JOB], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><CleanerSchedulePage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Morning Clean')).toBeInTheDocument();
    });
  });

  it('shows empty state when no jobs scheduled', async () => {
    vi.mocked(jobRequestsApi.getCleanerSchedule).mockResolvedValue({ schedule: [], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><CleanerSchedulePage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText(/no upcoming jobs/i)).toBeInTheDocument();
    });
  });

  it('shows error alert when fetch fails', async () => {
    vi.mocked(jobRequestsApi.getCleanerSchedule).mockRejectedValue(new Error('Failed to load schedule.'));
    render(<MemoryRouter><CleanerSchedulePage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Failed to load schedule.')).toBeInTheDocument();
    });
  });

  it('renders Start Job button for confirmed jobs', async () => {
    vi.mocked(jobRequestsApi.getCleanerSchedule).mockResolvedValue({ schedule: [MOCK_JOB], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><CleanerSchedulePage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start job/i })).toBeInTheDocument();
    });
  });

  it('renders Cancel Job button for confirmed jobs', async () => {
    vi.mocked(jobRequestsApi.getCleanerSchedule).mockResolvedValue({ schedule: [MOCK_JOB], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><CleanerSchedulePage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /cancel job/i })).toBeInTheDocument();
    });
  });

  it('renders Mark Complete button for in_progress jobs', async () => {
    const inProgressJob = { ...MOCK_JOB, status: 'in_progress' as const };
    vi.mocked(jobRequestsApi.getCleanerSchedule).mockResolvedValue({ schedule: [inProgressJob], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><CleanerSchedulePage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /mark complete/i })).toBeInTheDocument();
    });
  });

  it('clicking Start Job calls updateJobStatus with in_progress', async () => {
    vi.mocked(jobRequestsApi.getCleanerSchedule).mockResolvedValue({ schedule: [MOCK_JOB], pagination: MOCK_PAGINATION });
    vi.mocked(jobRequestsApi.updateJobStatus).mockResolvedValue({
      message: 'ok',
      job_request: { ...MOCK_JOB, status: 'in_progress' as const },
    });
    render(<MemoryRouter><CleanerSchedulePage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /start job/i }));

    await userEvent.click(screen.getByRole('button', { name: /start job/i }));

    await waitFor(() => {
      expect(jobRequestsApi.updateJobStatus).toHaveBeenCalledWith(MOCK_JOB.id, 'in_progress', 'test-token');
    });
  });

  it('shows pagination controls when has_next is true', async () => {
    const pagedPagination = { page: 1, per_page: 25, total: 30, total_pages: 2, has_prev: false, has_next: true };
    vi.mocked(jobRequestsApi.getCleanerSchedule).mockResolvedValue({ schedule: [MOCK_JOB], pagination: pagedPagination });
    render(<MemoryRouter><CleanerSchedulePage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /next/i }));

    expect(screen.getByRole('button', { name: /next/i })).not.toBeDisabled();
    expect(screen.getByRole('button', { name: /previous/i })).toBeDisabled();
  });

  it('renders client email in the job card', async () => {
    vi.mocked(jobRequestsApi.getCleanerSchedule).mockResolvedValue({ schedule: [MOCK_JOB], pagination: MOCK_PAGINATION });
    render(<MemoryRouter><CleanerSchedulePage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('user@test.com')).toBeInTheDocument();
    });
  });
});

describe('CleanerSchedulePage – cancel', () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.restoreAllMocks());

  it('clicking Cancel Job with confirmation calls updateJobStatus with cancelled', async () => {
    vi.mocked(jobRequestsApi.getCleanerSchedule).mockResolvedValue({ schedule: [MOCK_JOB], pagination: MOCK_PAGINATION });
    vi.mocked(jobRequestsApi.updateJobStatus).mockResolvedValue({
      message: 'ok',
      job_request: { ...MOCK_JOB, status: 'cancelled' as const },
    });
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    render(<MemoryRouter><CleanerSchedulePage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /cancel job/i }));

    await userEvent.click(screen.getByRole('button', { name: /cancel job/i }));

    await waitFor(() => {
      expect(jobRequestsApi.updateJobStatus).toHaveBeenCalledWith(MOCK_JOB.id, 'cancelled', 'test-token');
    });
  });
});
