import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import EditJobRequestPage from './EditJobRequestPage';
import * as jobRequestsApi from '../api/job_requests';
import * as cleanersApi from '../api/cleaners';
import * as storage from '../auth/storage';

vi.mock('../api/job_requests', () => ({
  getJobRequest: vi.fn(),
  updateJobRequest: vi.fn(),
}));

vi.mock('../api/cleaners', () => ({
  listCleaners: vi.fn(),
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
  title: 'Office Clean',
  description: 'Clean the office.',
  service_type: 'full',
  location: '10 Shenton Way',
  status: 'pending',
  preferred_date: '2099-12-01',
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

describe('EditJobRequestPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(cleanersApi.listCleaners).mockResolvedValue({ cleaners: [] });
  });

  it('shows loading spinner initially', () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'u@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockReturnValue(new Promise(() => {}));
    render(<MemoryRouter><EditJobRequestPage /></MemoryRouter>);
    expect(document.querySelector('.spinner-border')).toBeInTheDocument();
  });

  it('renders the Edit Job Request heading for pending job', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'u@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: MOCK_JOB });
    render(<MemoryRouter><EditJobRequestPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Edit Job Request')).toBeInTheDocument();
    });
  });

  it('shows warning for non-pending job status', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'u@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({
      job_request: { ...MOCK_JOB, status: 'confirmed' },
    });
    render(<MemoryRouter><EditJobRequestPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText(/only pending job requests can be edited/i)).toBeInTheDocument();
    });
  });

  it('shows error when fetch fails', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'u@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockRejectedValue(
      new Error('Failed to load job request.')
    );
    render(<MemoryRouter><EditJobRequestPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Failed to load job request.')).toBeInTheDocument();
    });
  });

  it('redirects non-end_user away', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'cleaner@test.com', role: 'cleaner', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: MOCK_JOB });
    render(<MemoryRouter><EditJobRequestPage /></MemoryRouter>);
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/job-requests');
    });
  });

  it('calls updateJobRequest and navigates to /job-requests on successful save', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'u@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: MOCK_JOB });
    vi.mocked(jobRequestsApi.updateJobRequest).mockResolvedValue({ message: 'Updated.', job_request: MOCK_JOB });
    render(<MemoryRouter><EditJobRequestPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /save changes/i }));

    await userEvent.click(screen.getByRole('button', { name: /save changes/i }));

    await waitFor(() => {
      expect(jobRequestsApi.updateJobRequest).toHaveBeenCalledOnce();
      expect(mockNavigate).toHaveBeenCalledWith('/job-requests', { replace: true });
    });
  });

  it('shows title validation error when title is cleared', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'u@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: MOCK_JOB });
    render(<MemoryRouter><EditJobRequestPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /save changes/i }));

    await userEvent.clear(screen.getAllByRole('textbox')[0]);
    fireEvent.submit(document.querySelector('form')!);

    await waitFor(() => {
      expect(screen.getByText('Title is required.')).toBeInTheDocument();
    });
  });

  it('shows service type validation error when service type is cleared', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'u@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: MOCK_JOB });
    render(<MemoryRouter><EditJobRequestPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /save changes/i }));

    await userEvent.selectOptions(screen.getAllByRole('combobox')[0], '');
    fireEvent.submit(document.querySelector('form')!);

    await waitFor(() => {
      expect(screen.getByText('Service type is required.')).toBeInTheDocument();
    });
  });

  it('shows end time error when end time is not after start time', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'u@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: MOCK_JOB });
    render(<MemoryRouter><EditJobRequestPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /save changes/i }));

    const timeInputs = document.querySelectorAll('input[type="time"]');
    fireEvent.change(timeInputs[0], { target: { value: '14:00' } });
    fireEvent.change(timeInputs[1], { target: { value: '10:00' } });
    fireEvent.submit(document.querySelector('form')!);

    await waitFor(() => {
      expect(screen.getByText('End time must be strictly after start time.')).toBeInTheDocument();
    });
  });

  it('shows error when save fails', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'u@test.com', role: 'end_user', created_at: '' });
    vi.mocked(jobRequestsApi.getJobRequest).mockResolvedValue({ job_request: MOCK_JOB });
    vi.mocked(jobRequestsApi.updateJobRequest).mockRejectedValue(new Error('Failed to update job request.'));
    render(<MemoryRouter><EditJobRequestPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /save changes/i }));

    await userEvent.click(screen.getByRole('button', { name: /save changes/i }));

    await waitFor(() => {
      expect(screen.getByText('Failed to update job request.')).toBeInTheDocument();
    });
  });
});
