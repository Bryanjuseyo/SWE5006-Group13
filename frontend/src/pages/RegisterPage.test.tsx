import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import RegisterPage from './RegisterPage';

vi.mock('../api/auth', () => ({
  register: vi.fn(),
  login: vi.fn(),
  verify2FA: vi.fn(),
  resend2FA: vi.fn(),
}));

vi.mock('../auth/storage', () => ({
  getUser: vi.fn().mockReturnValue(null),
  clearAuth: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

const getPasswordInput = () =>
  document.querySelector('input[type="password"]') as HTMLInputElement;

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
