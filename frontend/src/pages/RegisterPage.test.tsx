import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import RegisterPage from './RegisterPage';
import * as authApi from '../api/auth';

vi.mock('../api/auth', () => ({
  register: vi.fn(),
  login: vi.fn(),
  verify2FA: vi.fn(),
  resend2FA: vi.fn(),
}));

vi.mock('../auth/storage', () => ({
  getUser: vi.fn().mockReturnValue(null),
  clearAuth: vi.fn(),
  setAuth: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

const getPasswordInput = () =>
  document.querySelector('input[type="password"]') as HTMLInputElement;

async function advanceToStep2(role: string = 'end_user') {
  render(<MemoryRouter><RegisterPage /></MemoryRouter>);
  const emailInputs = screen.getAllByRole('textbox');
  await userEvent.type(emailInputs[0], 'user@test.com');
  await userEvent.type(document.querySelector('input[type="password"]')!, 'Password1');
  if (role !== 'end_user') {
    await userEvent.selectOptions(screen.getByRole('combobox'), role);
  }
  await userEvent.click(screen.getByRole('button', { name: /next/i }));
  await waitFor(() => screen.getByText(/tell us a bit about yourself/i));
}

describe('RegisterPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders the Create an account heading', () => {
    render(<MemoryRouter><RegisterPage /></MemoryRouter>);
    expect(screen.getByText('Create an account')).toBeInTheDocument();
  });

  it('renders email, password fields and the Next button', () => {
    render(<MemoryRouter><RegisterPage /></MemoryRouter>);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(getPasswordInput()).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
  });

  it('shows error when invalid email is submitted', async () => {
    render(<MemoryRouter><RegisterPage /></MemoryRouter>);
    await userEvent.type(screen.getByRole('textbox'), 'not-an-email');
    await userEvent.type(getPasswordInput(), 'Password1');
    // fireEvent.submit bypasses HTML5 type="email" constraint validation
    fireEvent.submit(document.querySelector('form')!);
    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address.')).toBeInTheDocument();
    });
  });

  it('shows error when password does not meet requirements', async () => {
    render(<MemoryRouter><RegisterPage /></MemoryRouter>);
    await userEvent.type(screen.getByRole('textbox'), 'user@test.com');
    await userEvent.type(getPasswordInput(), 'weak');
    // Use fireEvent.submit to bypass HTML5 required validation; click would also work here
    fireEvent.submit(document.querySelector('form')!);
    await waitFor(() => {
      // Match the exact error message to avoid matching the "Password" label
      expect(
        screen.getByText('Password must be at least 8 characters and contain letters and numbers.')
      ).toBeInTheDocument();
    });
  });

  it('advances to step 2 with valid email and password', async () => {
    render(<MemoryRouter><RegisterPage /></MemoryRouter>);
    await userEvent.type(screen.getByRole('textbox'), 'user@test.com');
    await userEvent.type(getPasswordInput(), 'Password1');
    await userEvent.click(screen.getByRole('button', { name: /next/i }));
    await waitFor(() => {
      expect(screen.getByText(/tell us a bit about yourself/i)).toBeInTheDocument();
    });
  });

  it('renders a link to the login page', () => {
    render(<MemoryRouter><RegisterPage /></MemoryRouter>);
    // Navbar may also render a Login link; assert at least one points to /login
    const links = screen.getAllByRole('link', { name: /^login$/i });
    expect(links.some(l => l.getAttribute('href') === '/login')).toBe(true);
  });
});

describe('RegisterPage – step 2', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders first name and last name fields after advancing from step 1', async () => {
    await advanceToStep2();
    expect(screen.getByPlaceholderText(/jane/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/doe/i)).toBeInTheDocument();
  });

  it('shows error when first name is missing', async () => {
    await advanceToStep2();
    fireEvent.submit(document.querySelector('form')!);
    await waitFor(() => {
      expect(screen.getByText('First name and last name are required.')).toBeInTheDocument();
    });
  });

  it('shows error for invalid phone number', async () => {
    await advanceToStep2();
    await userEvent.type(screen.getByPlaceholderText(/jane/i), 'Jane');
    await userEvent.type(screen.getByPlaceholderText(/doe/i), 'Doe');
    await userEvent.type(screen.getByPlaceholderText(/8-digit/i), '1234567');
    fireEvent.submit(document.querySelector('form')!);
    await waitFor(() => {
      expect(screen.getByText('Phone must be 8 digits and start with 8 or 9.')).toBeInTheDocument();
    });
  });

  it('advances to step 3 when cleaner role selected', async () => {
    await advanceToStep2('cleaner');
    await userEvent.type(screen.getByPlaceholderText(/jane/i), 'Jane');
    await userEvent.type(screen.getByPlaceholderText(/doe/i), 'Doe');
    await userEvent.click(screen.getByRole('button', { name: /next: cleaner details/i }));
    await waitFor(() => {
      expect(screen.getByText(/service type/i)).toBeInTheDocument();
    });
  });

  it('calls register() when end_user submits step 2', async () => {
    vi.mocked(authApi.register).mockResolvedValue({ message: 'Registered.', requires_2fa: true, temp_token: 'tok123' });
    await advanceToStep2('end_user');
    await userEvent.type(screen.getByPlaceholderText(/jane/i), 'Jane');
    await userEvent.type(screen.getByPlaceholderText(/doe/i), 'Doe');
    await userEvent.click(screen.getByRole('button', { name: /complete registration/i }));
    await waitFor(() => {
      expect(authApi.register).toHaveBeenCalledOnce();
    });
  });
});

describe('RegisterPage – step 3 (cleaner)', () => {
  beforeEach(() => vi.clearAllMocks());

  async function advanceToStep3() {
    await advanceToStep2('cleaner');
    await userEvent.type(screen.getByPlaceholderText(/jane/i), 'Jane');
    await userEvent.type(screen.getByPlaceholderText(/doe/i), 'Doe');
    await userEvent.click(screen.getByRole('button', { name: /next: cleaner details/i }));
    await waitFor(() => screen.getByText(/service type/i));
  }

  it('renders Service Type dropdown, Hourly Rate, and Years of Experience', async () => {
    await advanceToStep3();
    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/e\.g\. 25\.50/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('e.g. 2')).toBeInTheDocument();
  });

  it('shows error for negative years of experience', async () => {
    await advanceToStep3();
    const yearsInput = screen.getByPlaceholderText('e.g. 2');
    await userEvent.clear(yearsInput);
    await userEvent.type(yearsInput, '-1');
    fireEvent.submit(document.querySelector('form')!);
    await waitFor(() => {
      expect(screen.getByText('Years of experience must be a non-negative number.')).toBeInTheDocument();
    });
  });

  it('shows error when years of experience is more than 100', async () => {
    await advanceToStep3();
    const yearsInput = screen.getByPlaceholderText('e.g. 2');
    await userEvent.clear(yearsInput);
    await userEvent.type(yearsInput, '101');
    fireEvent.submit(document.querySelector('form')!);
    await waitFor(() => {
      expect(screen.getByText('Years of experience cannot be more than 100.')).toBeInTheDocument();
    });
  });

  it('shows error for negative hourly rate', async () => {
    await advanceToStep3();
    const rateInput = screen.getByPlaceholderText(/e\.g\. 25\.50/i);
    await userEvent.type(rateInput, '-5');
    fireEvent.submit(document.querySelector('form')!);
    await waitFor(() => {
      expect(screen.getByText('Hourly rate must be a non-negative number.')).toBeInTheDocument();
    });
  });

  it('calls register() and shows OTP step on successful cleaner registration', async () => {
    vi.mocked(authApi.register).mockResolvedValue({ message: 'Registered.', requires_2fa: true, temp_token: 'tok123' });
    await advanceToStep3();
    await userEvent.click(screen.getByRole('button', { name: /complete registration/i }));
    await waitFor(() => {
      expect(authApi.register).toHaveBeenCalledOnce();
      expect(screen.getByText(/verify your email/i)).toBeInTheDocument();
    });
  });
});

describe('RegisterPage – OTP step', () => {
  beforeEach(() => vi.clearAllMocks());

  async function reachOtpStep() {
    vi.mocked(authApi.register).mockResolvedValue({ message: 'Registered.', requires_2fa: true, temp_token: 'tok123' });
    render(<MemoryRouter><RegisterPage /></MemoryRouter>);
    const emailInputs = screen.getAllByRole('textbox');
    await userEvent.type(emailInputs[0], 'user@test.com');
    await userEvent.type(document.querySelector('input[type="password"]')!, 'Password1');
    await userEvent.click(screen.getByRole('button', { name: /next/i }));
    await waitFor(() => screen.getByText(/tell us a bit about yourself/i));
    await userEvent.type(screen.getByPlaceholderText(/jane/i), 'Jane');
    await userEvent.type(screen.getByPlaceholderText(/doe/i), 'Doe');
    await userEvent.click(screen.getByRole('button', { name: /complete registration/i }));
    await waitFor(() => screen.getByText(/verify your email/i));
  }

  it('shows "Verify your email" heading when tempToken is set', async () => {
    await reachOtpStep();
    expect(screen.getByRole('heading', { name: /verify your email/i })).toBeInTheDocument();
  });

  it('calls verify2FA and navigates to /dashboard on success', async () => {
    vi.mocked(authApi.verify2FA).mockResolvedValue({
      message: 'ok',
      token: 'jwt-token',
      user: { id: 1, email: 'user@test.com', role: 'end_user', created_at: '', two_factor_enabled: false },
    });
    await reachOtpStep();
    await userEvent.type(screen.getByPlaceholderText('000000'), '123456');
    await userEvent.click(screen.getByRole('button', { name: /complete registration/i }));
    await waitFor(() => {
      expect(authApi.verify2FA).toHaveBeenCalledWith('123456', 'tok123');
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
    });
  });

  it('shows error message when verify2FA fails', async () => {
    vi.mocked(authApi.verify2FA).mockRejectedValue(new Error('Invalid OTP code.'));
    await reachOtpStep();
    await userEvent.type(screen.getByPlaceholderText('000000'), '000000');
    await userEvent.click(screen.getByRole('button', { name: /complete registration/i }));
    await waitFor(() => {
      expect(screen.getByText('Invalid OTP code.')).toBeInTheDocument();
    });
  });
});
