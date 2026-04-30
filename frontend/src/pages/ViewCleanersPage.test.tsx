import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ViewCleanersPage from './ViewCleanersPage';
import * as cleanersApi from '../api/cleaners';

vi.mock('../api/cleaners', () => ({
  listCleaners: vi.fn(),
}));

vi.mock('../auth/storage', () => ({
  getUser: vi.fn().mockReturnValue(null),
  clearAuth: vi.fn(),
}));

const MOCK_CLEANER: cleanersApi.CleanerListItem = {
  user_id: 1,
  first_name: 'Alice',
  last_name: 'Smith',
  email: 'alice@test.com',
  city: 'Singapore',
  cleaner_profile: {
    id: 10,
    user_id: 1,
    service_type: 'full',
    hourly_rate: 25,
    years_experience: 3,
    offered_services: [],
  },
};

describe('ViewCleanersPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('shows loading state while fetching', () => {
    vi.mocked(cleanersApi.listCleaners).mockReturnValue(new Promise(() => {}));
    render(<MemoryRouter><ViewCleanersPage /></MemoryRouter>);
    expect(screen.getByText(/loading cleaners/i)).toBeInTheDocument();
  });

  it('renders cleaner cards after fetch', async () => {
    vi.mocked(cleanersApi.listCleaners).mockResolvedValue({ cleaners: [MOCK_CLEANER] });
    render(<MemoryRouter><ViewCleanersPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Alice Smith')).toBeInTheDocument();
    });
  });

  it('shows empty state when no cleaners found', async () => {
    vi.mocked(cleanersApi.listCleaners).mockResolvedValue({ cleaners: [] });
    render(<MemoryRouter><ViewCleanersPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText(/no cleaners found/i)).toBeInTheDocument();
    });
  });

  it('shows error alert when fetch fails', async () => {
    vi.mocked(cleanersApi.listCleaners).mockRejectedValue(new Error('Failed to load cleaners'));
    render(<MemoryRouter><ViewCleanersPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Failed to load cleaners')).toBeInTheDocument();
    });
  });

  it('filters cleaners by search query', async () => {
    vi.mocked(cleanersApi.listCleaners).mockResolvedValue({
      cleaners: [
        MOCK_CLEANER,
        { ...MOCK_CLEANER, user_id: 2, first_name: 'Bob', last_name: 'Jones', email: 'bob@test.com' },
      ],
    });
    render(<MemoryRouter><ViewCleanersPage /></MemoryRouter>);
    await waitFor(() => screen.getByText('Alice Smith'));

    const search = screen.getByPlaceholderText(/search by name/i);
    await userEvent.type(search, 'Bob');

    expect(screen.queryByText('Alice Smith')).not.toBeInTheDocument();
    expect(screen.getByText('Bob Jones')).toBeInTheDocument();
  });
});
