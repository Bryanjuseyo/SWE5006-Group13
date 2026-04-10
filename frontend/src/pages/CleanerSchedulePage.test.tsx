import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
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

describe('CleanerSchedulePage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('shows loading spinner while fetching', () => {
    vi.mocked(jobRequestsApi.getCleanerSchedule).mockReturnValue(new Promise(() => {}));
    render(<MemoryRouter><CleanerSchedulePage /></MemoryRouter>);
    expect(document.querySelector('.spinner-border')).toBeInTheDocument();
  });

  it('renders job cards after fetch', async () => {
    vi.mocked(jobRequestsApi.getCleanerSchedule).mockResolvedValue({ schedule: [MOCK_JOB] });
    render(<MemoryRouter><CleanerSchedulePage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Morning Clean')).toBeInTheDocument();
    });
  });

  it('shows empty state when no jobs scheduled', async () => {
    vi.mocked(jobRequestsApi.getCleanerSchedule).mockResolvedValue({ schedule: [] });
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
    vi.mocked(jobRequestsApi.getCleanerSchedule).mockResolvedValue({ schedule: [MOCK_JOB] });
    render(<MemoryRouter><CleanerSchedulePage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start job/i })).toBeInTheDocument();
    });
  });
});
