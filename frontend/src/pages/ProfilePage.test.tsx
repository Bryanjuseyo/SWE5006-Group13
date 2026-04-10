import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ProfilePage from './ProfilePage';
import * as profileApi from '../api/profile';

vi.mock('../api/profile', () => ({
  getMyProfile: vi.fn(),
  updateMyProfile: vi.fn(),
}));

vi.mock('../auth/storage', () => ({
  getUser: vi.fn().mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' }),
  clearAuth: vi.fn(),
}));

const MOCK_PROFILE: profileApi.GetProfileResponse = {
  email: 'user@test.com',
  role: 'end_user',
  created_at: '2024-01-01T00:00:00Z',
  profile: { id: 1, user_id: 1, first_name: 'Jane', last_name: 'Doe', phone: null, address: null, city: null },
};

describe('ProfilePage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('shows loading text while fetching', () => {
    vi.mocked(profileApi.getMyProfile).mockReturnValue(new Promise(() => {}));
    render(<MemoryRouter><ProfilePage /></MemoryRouter>);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders the My Profile heading after load', async () => {
    vi.mocked(profileApi.getMyProfile).mockResolvedValue(MOCK_PROFILE);
    render(<MemoryRouter><ProfilePage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('My Profile')).toBeInTheDocument();
    });
  });

  it('displays user email after load', async () => {
    vi.mocked(profileApi.getMyProfile).mockResolvedValue(MOCK_PROFILE);
    render(<MemoryRouter><ProfilePage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('user@test.com')).toBeInTheDocument();
    });
  });

  it('shows error alert when fetch fails', async () => {
    vi.mocked(profileApi.getMyProfile).mockRejectedValue(new Error('Failed to load profile.'));
    render(<MemoryRouter><ProfilePage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Failed to load profile.')).toBeInTheDocument();
    });
  });

  it('shows validation error when first name is empty on save', async () => {
    vi.mocked(profileApi.getMyProfile).mockResolvedValue(MOCK_PROFILE);
    render(<MemoryRouter><ProfilePage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /save profile/i }));

    // Clear first name field
    const inputs = document.querySelectorAll('input.form-control');
    const firstNameInput = inputs[0] as HTMLInputElement;
    await userEvent.clear(firstNameInput);
    await userEvent.click(screen.getByRole('button', { name: /save profile/i }));

    await waitFor(() => {
      expect(screen.getByText(/first name and last name are required/i)).toBeInTheDocument();
    });
  });
});
