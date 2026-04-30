/**
 * Page tests — src/pages/LoginPage.tsx
 *
 * NOTE on selectors:
 *   The LoginPage labels do NOT use htmlFor / input id pairs, so
 *   getByLabelText() cannot resolve the associated control.
 *   Instead we use:
 *     - getByRole('textbox')         for type="email" (only textbox in credentials form)
 *     - document.querySelector(...)  for type="password" (no ARIA role)
 *     - getByRole('textbox')         for the OTP input (only textbox in 2FA form)
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import LoginPage from './LoginPage';
import * as authApi from '../api/auth';
import * as storage from '../auth/storage';

vi.mock('../api/auth', () => ({
  login: vi.fn(),
  verify2FA: vi.fn(),
  resend2FA: vi.fn(),
}));

vi.mock('../auth/storage', () => ({
  getUser: vi.fn().mockReturnValue(null), // Navbar shows logged-out state
  setAuth: vi.fn(),
  clearAuth: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

/** Grab the password input (type="password" has no ARIA role). */
const getPasswordInput = () =>
  document.querySelector('input[type="password"]') as HTMLInputElement;

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders email and password fields', () => {
    render(<MemoryRouter><LoginPage /></MemoryRouter>);

    // type="email" maps to ARIA role "textbox"
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    // type="password" has no ARIA role — query directly
    expect(getPasswordInput()).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^login$/i })).toBeInTheDocument();
  });

  it('calls setAuth and navigates to /dashboard on successful login', async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      message: 'Login successful.',
      token: 'jwt-abc',
      user: {
        id: 1,
        email: 'u@test.com',
        role: 'end_user',
        created_at: '2024-01-01',
        two_factor_enabled: true,
      },
    });

    render(<MemoryRouter><LoginPage /></MemoryRouter>);
    await userEvent.type(screen.getByRole('textbox'), 'u@test.com');
    await userEvent.type(getPasswordInput(), 'Password1');
    await userEvent.click(screen.getByRole('button', { name: /^login$/i }));

    await waitFor(() => {
      expect(storage.setAuth).toHaveBeenCalledWith(
        'jwt-abc',
        expect.objectContaining({ email: 'u@test.com' })
      );
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
    });
  });

  it('shows an error alert when credentials are rejected', async () => {
    vi.mocked(authApi.login).mockRejectedValue(new Error('Invalid email or password.'));

    render(<MemoryRouter><LoginPage /></MemoryRouter>);
    await userEvent.type(screen.getByRole('textbox'), 'bad@test.com');
    await userEvent.type(getPasswordInput(), 'wrong');
    await userEvent.click(screen.getByRole('button', { name: /^login$/i }));

    await waitFor(() => {
      expect(screen.getByText('Invalid email or password.')).toBeInTheDocument();
    });
  });

  it('transitions to the OTP form when the server requires 2FA', async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      message: 'OTP sent.',
      requires_2fa: true,
      temp_token: 'temp-123',
    });

    render(<MemoryRouter><LoginPage /></MemoryRouter>);
    await userEvent.type(screen.getByRole('textbox'), 'u@test.com');
    await userEvent.type(getPasswordInput(), 'Password1');
    await userEvent.click(screen.getByRole('button', { name: /^login$/i }));

    await waitFor(() => {
      // Credentials form is gone; OTP textbox (type="text") is now the only textbox
      expect(screen.getByRole('textbox')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /verify code/i })).toBeInTheDocument();
    });
  });

  it('shows an error when OTP verification fails', async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      message: 'OTP sent.',
      requires_2fa: true,
      temp_token: 'temp-123',
    });
    vi.mocked(authApi.verify2FA).mockRejectedValue(
      new Error('Incorrect OTP. Please try again.')
    );

    render(<MemoryRouter><LoginPage /></MemoryRouter>);

    // Step 1: submit credentials to reach OTP form
    await userEvent.type(screen.getByRole('textbox'), 'u@test.com');
    await userEvent.type(getPasswordInput(), 'Password1');
    await userEvent.click(screen.getByRole('button', { name: /^login$/i }));
    await waitFor(() => screen.getByRole('button', { name: /verify code/i }));

    // Step 2: submit wrong OTP — the only textbox on this step is the OTP input
    await userEvent.type(screen.getByRole('textbox'), '000000');
    await userEvent.click(screen.getByRole('button', { name: /verify code/i }));

    await waitFor(() => {
      expect(screen.getByText('Incorrect OTP. Please try again.')).toBeInTheDocument();
    });
  });
});
