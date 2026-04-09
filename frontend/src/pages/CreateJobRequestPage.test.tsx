import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import CreateJobRequestPage from './CreateJobRequestPage';
import * as jobRequestsApi from '../api/job_requests';
import * as cleanersApi from '../api/cleaners';
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
});
