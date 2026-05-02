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

  it('submitting OTP calls enable2FA', async () => {
    vi.mocked(authApi.get2FAStatus).mockResolvedValue({ two_factor_enabled: false });
    vi.mocked(authApi.setup2FA).mockResolvedValue({ message: 'OTP sent.' });
    vi.mocked(authApi.enable2FA).mockResolvedValue({ message: '2FA enabled.' });
    render(<MemoryRouter><TwoFactorSetupPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /send verification code/i }));

    await userEvent.click(screen.getByRole('button', { name: /send verification code/i }));
    await waitFor(() => screen.getByRole('button', { name: /enable 2fa/i }));

    await userEvent.type(screen.getByPlaceholderText('000000'), '123456');
    await userEvent.click(screen.getByRole('button', { name: /enable 2fa/i }));

    await waitFor(() => {
      expect(authApi.enable2FA).toHaveBeenCalledWith('123456', 'test-token');
    });
  });

  it('enable2FA failure shows error alert', async () => {
    vi.mocked(authApi.get2FAStatus).mockResolvedValue({ two_factor_enabled: false });
    vi.mocked(authApi.setup2FA).mockResolvedValue({ message: 'OTP sent.' });
    vi.mocked(authApi.enable2FA).mockRejectedValue(new Error('Invalid OTP.'));
    render(<MemoryRouter><TwoFactorSetupPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /send verification code/i }));

    await userEvent.click(screen.getByRole('button', { name: /send verification code/i }));
    await waitFor(() => screen.getByRole('button', { name: /enable 2fa/i }));

    await userEvent.type(screen.getByPlaceholderText('000000'), '000000');
    await userEvent.click(screen.getByRole('button', { name: /enable 2fa/i }));

    await waitFor(() => {
      expect(screen.getByText('Invalid OTP.')).toBeInTheDocument();
    });
  });

  it('submitting disable form calls disable2FA', async () => {
    vi.mocked(authApi.get2FAStatus).mockResolvedValue({ two_factor_enabled: true });
    vi.mocked(authApi.disable2FA).mockResolvedValue({ message: 'Disabled.' });
    render(<MemoryRouter><TwoFactorSetupPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /disable 2fa/i }));

    await userEvent.type(document.querySelector('input[type="password"]') as HTMLElement, 'MyPassword1');
    await userEvent.click(screen.getByRole('button', { name: /disable 2fa/i }));

    await waitFor(() => {
      expect(authApi.disable2FA).toHaveBeenCalledWith('MyPassword1', 'test-token');
    });
  });

  it('disable2FA failure shows error alert', async () => {
    vi.mocked(authApi.get2FAStatus).mockResolvedValue({ two_factor_enabled: true });
    vi.mocked(authApi.disable2FA).mockRejectedValue(new Error('Wrong password.'));
    render(<MemoryRouter><TwoFactorSetupPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /disable 2fa/i }));

    await userEvent.type(document.querySelector('input[type="password"]') as HTMLElement, 'wrong');
    await userEvent.click(screen.getByRole('button', { name: /disable 2fa/i }));

    await waitFor(() => {
      expect(screen.getByText('Wrong password.')).toBeInTheDocument();
    });
  });
});
