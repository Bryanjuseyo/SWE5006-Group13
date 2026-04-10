import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import CleanerAvailabilityPage from './CleanerAvailabilityPage';
import * as availabilityApi from '../api/cleanerAvailability';

vi.mock('../api/cleanerAvailability', () => ({
  getAvailability: vi.fn(),
  addAvailability: vi.fn(),
  updateAvailability: vi.fn(),
  deleteAvailability: vi.fn(),
}));

vi.mock('../auth/storage', () => ({
  getUser: vi.fn().mockReturnValue({ id: 2, email: 'cleaner@test.com', role: 'cleaner', created_at: '' }),
  clearAuth: vi.fn(),
}));

const MOCK_SLOT: availabilityApi.AvailabilitySlot = {
  id: 1,
  cleaner_profile_id: 10,
  start_date: '2099-09-01',
  end_date: '2099-09-30',
  start_time: '09:00:00',
  end_time: '17:00:00',
};

describe('CleanerAvailabilityPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders the page heading', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [] });
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Availability Management')).toBeInTheDocument();
    });
  });

  it('renders availability slots after fetch', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [MOCK_SLOT] });
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText(/your availability slots/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no slots set', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [] });
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText(/no availability slots set/i)).toBeInTheDocument();
    });
  });

  it('shows error alert when fetch fails', async () => {
    vi.mocked(availabilityApi.getAvailability).mockRejectedValue(new Error('Failed to load availability.'));
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Failed to load availability.')).toBeInTheDocument();
    });
  });

  it('renders the Add Slot button', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [] });
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /add slot/i })).toBeInTheDocument();
    });
  });
});
