import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import TwoFactorSetupPage from './TwoFactorSetupPage';
import * as authApi from '../api/auth';

vi.mock('../api/auth', () => ({
  get2FAStatus: vi.fn(),
  setup2FA: vi.fn(),
  enable2FA: vi.fn(),
  disable2FA: vi.fn(),
}));

vi.mock('../auth/storage', () => ({
  getToken: vi.fn().mockReturnValue('test-token'),
  getUser: vi.fn().mockReturnValue({ id: 1, email: 'user@test.com', role: 'end_user', created_at: '' }),
  clearAuth: vi.fn(),
}));

describe('TwoFactorSetupPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('shows loading text while fetching status', () => {
    vi.mocked(authApi.get2FAStatus).mockReturnValue(new Promise(() => {}));
    render(<MemoryRouter><TwoFactorSetupPage /></MemoryRouter>);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders the 2FA heading after status loads', async () => {
    vi.mocked(authApi.get2FAStatus).mockResolvedValue({ two_factor_enabled: false });
    render(<MemoryRouter><TwoFactorSetupPage /></MemoryRouter>);
    await waitFor(() => {
      // Use getByRole to distinguish the h1 from the breadcrumb li with the same text
      expect(screen.getByRole('heading', { name: /two-factor authentication/i })).toBeInTheDocument();
    });
  });

  it('shows Disabled badge when 2FA is off', async () => {
    vi.mocked(authApi.get2FAStatus).mockResolvedValue({ two_factor_enabled: false });
    render(<MemoryRouter><TwoFactorSetupPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Disabled')).toBeInTheDocument();
    });
  });

  it('shows Enabled badge and disable form when 2FA is on', async () => {
    vi.mocked(authApi.get2FAStatus).mockResolvedValue({ two_factor_enabled: true });
    render(<MemoryRouter><TwoFactorSetupPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Enabled')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /disable 2fa/i })).toBeInTheDocument();
    });
  });

  it('shows error alert when status fetch fails', async () => {
    vi.mocked(authApi.get2FAStatus).mockRejectedValue(new Error('Failed to load 2FA status.'));
    render(<MemoryRouter><TwoFactorSetupPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Failed to load 2FA status.')).toBeInTheDocument();
    });
  });

  it('renders Send Verification Code button when 2FA is disabled', async () => {
    vi.mocked(authApi.get2FAStatus).mockResolvedValue({ two_factor_enabled: false });
    render(<MemoryRouter><TwoFactorSetupPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /send verification code/i })).toBeInTheDocument();
    });
  });

  it('shows OTP input after clicking Send Verification Code', async () => {
    vi.mocked(authApi.get2FAStatus).mockResolvedValue({ two_factor_enabled: false });
    vi.mocked(authApi.setup2FA).mockResolvedValue({ message: 'OTP sent.' });
    render(<MemoryRouter><TwoFactorSetupPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /send verification code/i }));

    await userEvent.click(screen.getByRole('button', { name: /send verification code/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /enable 2fa/i })).toBeInTheDocument();
    });
  });
});
