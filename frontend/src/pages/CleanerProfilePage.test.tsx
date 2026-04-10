import { render, screen, waitFor } from '@testing-library/react';
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
      // Use getByRole to avoid matching the Navbar "Cleaner Profile" link
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
});
