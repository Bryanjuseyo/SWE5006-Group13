import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import CleanerProfilePage from './CleanerProfilePage';
import * as cleanerProfileApi from '../api/cleanerProfile';

vi.mock('../api/cleanerProfile', () => ({
  getCleanerProfile: vi.fn(),
  updateCleanerProfile: vi.fn(),
}));

vi.mock('../auth/storage', () => ({
  getUser: vi.fn().mockReturnValue({ id: 2, email: 'cleaner@test.com', role: 'cleaner', created_at: '' }),
  clearAuth: vi.fn(),
}));

const MOCK_PROFILE: cleanerProfileApi.CleanerProfile = {
  id: 1,
  user_id: 2,
  service_type: 'full',
  hourly_rate: 30,
  years_experience: 5,
};

describe('CleanerProfilePage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('shows loading text while fetching', () => {
    vi.mocked(cleanerProfileApi.getCleanerProfile).mockReturnValue(new Promise(() => {}));
    render(<MemoryRouter><CleanerProfilePage /></MemoryRouter>);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders the Cleaner Profile heading after load', async () => {
    vi.mocked(cleanerProfileApi.getCleanerProfile).mockResolvedValue({ profile: null });
    render(<MemoryRouter><CleanerProfilePage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /cleaner profile/i })).toBeInTheDocument();
    });
  });

  it('renders the Save Cleaner Profile button after load', async () => {
    vi.mocked(cleanerProfileApi.getCleanerProfile).mockResolvedValue({ profile: null });
    render(<MemoryRouter><CleanerProfilePage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /save cleaner profile/i })).toBeInTheDocument();
    });
  });

  it('shows error alert when fetch fails', async () => {
    vi.mocked(cleanerProfileApi.getCleanerProfile).mockRejectedValue(
      new Error('Failed to load cleaner profile.')
    );
    render(<MemoryRouter><CleanerProfilePage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Failed to load cleaner profile.')).toBeInTheDocument();
    });
  });

  it('renders with existing profile data', async () => {
    vi.mocked(cleanerProfileApi.getCleanerProfile).mockResolvedValue({
      profile: { id: 1, user_id: 2, service_type: 'full', hourly_rate: 30, years_experience: 5 },
    });
    render(<MemoryRouter><CleanerProfilePage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /save cleaner profile/i })).toBeInTheDocument();
    });
  });

  it('populates form fields with fetched profile data', async () => {
    vi.mocked(cleanerProfileApi.getCleanerProfile).mockResolvedValue({ profile: MOCK_PROFILE });
    render(<MemoryRouter><CleanerProfilePage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /save cleaner profile/i }));

    expect((screen.getByRole('combobox') as HTMLSelectElement).value).toBe('full');
    expect((screen.getByPlaceholderText(/e\.g\. 25\.50/i) as HTMLInputElement).value).toBe('30');
    expect((screen.getByPlaceholderText('e.g. 2') as HTMLInputElement).value).toBe('5');
  });

  it('calls updateCleanerProfile when form is submitted', async () => {
    vi.mocked(cleanerProfileApi.getCleanerProfile).mockResolvedValue({ profile: MOCK_PROFILE });
    vi.mocked(cleanerProfileApi.updateCleanerProfile).mockResolvedValue({
      message: 'ok',
      profile: MOCK_PROFILE,
    });
    render(<MemoryRouter><CleanerProfilePage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /save cleaner profile/i }));

    await userEvent.click(screen.getByRole('button', { name: /save cleaner profile/i }));

    await waitFor(() => {
      expect(cleanerProfileApi.updateCleanerProfile).toHaveBeenCalledOnce();
    });
  });

  it('shows success message after update', async () => {
    vi.mocked(cleanerProfileApi.getCleanerProfile).mockResolvedValue({ profile: MOCK_PROFILE });
    vi.mocked(cleanerProfileApi.updateCleanerProfile).mockResolvedValue({
      message: 'ok',
      profile: MOCK_PROFILE,
    });
    render(<MemoryRouter><CleanerProfilePage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /save cleaner profile/i }));

    await userEvent.click(screen.getByRole('button', { name: /save cleaner profile/i }));

    await waitFor(() => {
      expect(screen.getByText('Cleaner profile saved.')).toBeInTheDocument();
    });
  });

  it('shows error when update fails', async () => {
    vi.mocked(cleanerProfileApi.getCleanerProfile).mockResolvedValue({ profile: MOCK_PROFILE });
    vi.mocked(cleanerProfileApi.updateCleanerProfile).mockRejectedValue(
      new Error('Failed to save cleaner profile.')
    );
    render(<MemoryRouter><CleanerProfilePage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /save cleaner profile/i }));

    await userEvent.click(screen.getByRole('button', { name: /save cleaner profile/i }));

    await waitFor(() => {
      expect(screen.getByText('Failed to save cleaner profile.')).toBeInTheDocument();
    });
  });

  it('shows error for negative years of experience', async () => {
    vi.mocked(cleanerProfileApi.getCleanerProfile).mockResolvedValue({ profile: MOCK_PROFILE });
    render(<MemoryRouter><CleanerProfilePage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /save cleaner profile/i }));

    const yearsInput = screen.getByPlaceholderText('e.g. 2');
    await userEvent.clear(yearsInput);
    await userEvent.type(yearsInput, '-1');
    fireEvent.submit(document.querySelector('form')!);

    await waitFor(() => {
      expect(screen.getByText('Years of experience must be a non-negative integer.')).toBeInTheDocument();
    });
  });

  it('shows error when years of experience is more than 100', async () => {
    vi.mocked(cleanerProfileApi.getCleanerProfile).mockResolvedValue({ profile: MOCK_PROFILE });
    render(<MemoryRouter><CleanerProfilePage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /save cleaner profile/i }));

    const yearsInput = screen.getByPlaceholderText('e.g. 2');
    await userEvent.clear(yearsInput);
    await userEvent.type(yearsInput, '101');
    fireEvent.submit(document.querySelector('form')!);

    await waitFor(() => {
      expect(screen.getByText('Years of experience cannot be more than 100.')).toBeInTheDocument();
    });
  });

  it('shows error for negative hourly rate', async () => {
    vi.mocked(cleanerProfileApi.getCleanerProfile).mockResolvedValue({ profile: MOCK_PROFILE });
    render(<MemoryRouter><CleanerProfilePage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /save cleaner profile/i }));

    const rateInput = screen.getByPlaceholderText(/e\.g\. 25\.50/i);
    await userEvent.clear(rateInput);
    await userEvent.type(rateInput, '-5');
    fireEvent.submit(document.querySelector('form')!);

    await waitFor(() => {
      expect(screen.getByText('Hourly rate must be a non-negative number.')).toBeInTheDocument();
    });
  });
});
