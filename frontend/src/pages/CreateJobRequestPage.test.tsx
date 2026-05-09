import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import CreateJobRequestPage from './CreateJobRequestPage';
import * as cleanersApi from '../api/cleaners';
import * as jobRequestsApi from '../api/job_requests';
import * as adminApi from '../api/admin';
import * as storage from '../auth/storage';

vi.mock('../api/job_requests', () => ({
  createJobRequest: vi.fn(),
}));

vi.mock('../api/cleaners', () => ({
  listCleaners: vi.fn(),
}));

vi.mock('../api/admin', () => ({
  autoAssignCleaner: vi.fn(),
  getAdminStats: vi.fn(),
  getAdminBookings: vi.fn(),
  rejectBooking: vi.fn(),
  getAdminUsers: vi.fn(),
  banUser: vi.fn(),
  unbanUser: vi.fn(),
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

describe('CreateJobRequestPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(cleanersApi.listCleaners).mockResolvedValue({ cleaners: [] });
  });

  it('renders the Create Job Request heading for end_user', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    render(<MemoryRouter><CreateJobRequestPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Create Job Request')).toBeInTheDocument();
    });
  });

  it('shows error when submitting with empty title', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    render(<MemoryRouter><CreateJobRequestPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /create job request/i }));

    // Use fireEvent.submit to bypass HTML5 required constraint validation
    fireEvent.submit(document.querySelector('form')!);
    await waitFor(() => {
      expect(screen.getByText('Title is required.')).toBeInTheDocument();
    });
  });

  it('renders Auto-match and Choose a cleaner toggle buttons', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    render(<MemoryRouter><CreateJobRequestPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /auto-match/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /choose a cleaner/i })).toBeInTheDocument();
    });
  });

  it('redirects non-end_user roles away from page', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 2, email: 'cleaner@test.com', role: 'cleaner', created_at: '' });
    render(<MemoryRouter><CreateJobRequestPage /></MemoryRouter>);
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/job-requests');
    });
  });

  it('shows service type required error when service type is missing', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    render(<MemoryRouter><CreateJobRequestPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /create job request/i }));

    // Fill title but leave service type empty; use fireEvent.submit to bypass HTML5 validation
    const textboxes = screen.getAllByRole('textbox');
    await userEvent.type(textboxes[0], 'Test Job');
    fireEvent.submit(document.querySelector('form')!);
    await waitFor(() => {
      expect(screen.getByText('Service type is required.')).toBeInTheDocument();
    });
  });

  it('shows location required error when title and service type are filled but not location', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    render(<MemoryRouter><CreateJobRequestPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /create job request/i }));

    await userEvent.type(screen.getAllByRole('textbox')[0], 'Test Job');
    await userEvent.selectOptions(screen.getByRole('combobox'), 'partial');
    fireEvent.submit(document.querySelector('form')!);
    await waitFor(() => {
      expect(screen.getByText('Location is required.')).toBeInTheDocument();
    });
  });

  it('shows date required error when title, service type, and location are filled but not date', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    render(<MemoryRouter><CreateJobRequestPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /create job request/i }));

    const textboxes = screen.getAllByRole('textbox');
    await userEvent.type(textboxes[0], 'Test Job');
    await userEvent.selectOptions(screen.getByRole('combobox'), 'full');
    await userEvent.type(textboxes[2], '10 Orchard Rd');
    fireEvent.submit(document.querySelector('form')!);
    await waitFor(() => {
      expect(screen.getByText('Preferred date is required.')).toBeInTheDocument();
    });
  });

  it('shows end time error when end time is not strictly after start time', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    render(<MemoryRouter><CreateJobRequestPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /create job request/i }));

    const textboxes = screen.getAllByRole('textbox');
    await userEvent.type(textboxes[0], 'Test Job');
    await userEvent.selectOptions(screen.getByRole('combobox'), 'full');
    await userEvent.type(textboxes[2], '10 Orchard Rd');
    fireEvent.change(document.querySelector('input[type="date"]')!, { target: { value: '2099-12-01' } });
    const timeInputs = document.querySelectorAll('input[type="time"]');
    fireEvent.change(timeInputs[0], { target: { value: '14:00' } });
    fireEvent.change(timeInputs[1], { target: { value: '10:00' } });
    fireEvent.submit(document.querySelector('form')!);
    await waitFor(() => {
      expect(screen.getByText('End time must be strictly after start time.')).toBeInTheDocument();
    });
  });

  it('calls createJobRequest and navigates to /job-requests on successful submission', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    const mockJob: jobRequestsApi.JobRequest = {
      id: 99, title: 'Test Job', description: null, service_type: 'partial',
      location: '10 Orchard Rd', preferred_date: '2099-12-01',
      preferred_time_start: null, preferred_time_end: null, status: 'pending',
      end_user_id: 1, cleaner_id: null, cleaner: null, end_user: null,
      is_in_priority_window: false, priority_window_end: null,
      created_at: '', updated_at: '',
    };
    vi.mocked(jobRequestsApi.createJobRequest).mockResolvedValue({ message: 'Created.', job_request: mockJob });
    vi.mocked(adminApi.autoAssignCleaner).mockResolvedValue({
      message: 'Assigned.', job_request: mockJob,
      assigned_cleaner: { cleaner_id: 5, email: 'c@test.com', name: 'Bob', service_type: 'partial', hourly_rate: 25, years_experience: 3 },
      strategy: 'default',
    });

    render(<MemoryRouter><CreateJobRequestPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /create job request/i }));

    const textboxes = screen.getAllByRole('textbox');
    await userEvent.type(textboxes[0], 'Test Job');
    await userEvent.selectOptions(screen.getByRole('combobox'), 'partial');
    await userEvent.type(textboxes[2], '10 Orchard Rd');
    fireEvent.change(document.querySelector('input[type="date"]')!, { target: { value: '2099-12-01' } });
    await userEvent.click(screen.getByRole('button', { name: /create job request/i }));

    await waitFor(() => {
      expect(jobRequestsApi.createJobRequest).toHaveBeenCalledOnce();
      expect(mockNavigate).toHaveBeenCalledWith('/job-requests', { replace: true });
    });
  });

  it('shows cleaner dropdown when "Choose a cleaner" mode is selected', async () => {
    vi.mocked(storage.getUser).mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' });
    render(<MemoryRouter><CreateJobRequestPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /choose a cleaner/i }));

    await userEvent.click(screen.getByRole('button', { name: /choose a cleaner/i }));

    await waitFor(() => {
      expect(screen.getByText(/only showing cleaners/i)).toBeInTheDocument();
    });
  });
});
