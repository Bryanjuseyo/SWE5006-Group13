import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import CleanerDashboard from './CleanerDashboard';

vi.mock('../auth/storage', () => ({
  getUser: vi.fn().mockReturnValue({
    id: 2, email: 'cleaner@test.com', role: 'cleaner', created_at: '',
  }),
  clearAuth: vi.fn(),
}));

describe('CleanerDashboard', () => {
  it('renders the Cleaner Dashboard heading', () => {
    render(<MemoryRouter><CleanerDashboard /></MemoryRouter>);
    expect(screen.getByText('Cleaner Dashboard')).toBeInTheDocument();
  });

  it('renders the Service Setup card', () => {
    render(<MemoryRouter><CleanerDashboard /></MemoryRouter>);
    expect(screen.getByText('Service Setup')).toBeInTheDocument();
  });

  it('renders the Browse Jobs card', () => {
    render(<MemoryRouter><CleanerDashboard /></MemoryRouter>);
    expect(screen.getByText('Browse Jobs')).toBeInTheDocument();
  });

  it('renders navigation links for cleaner sections', () => {
    render(<MemoryRouter><CleanerDashboard /></MemoryRouter>);
    expect(screen.getByRole('link', { name: /edit profile/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /manage availability/i })).toBeInTheDocument();
  });

  it('renders the Upcoming Schedule card', () => {
    render(<MemoryRouter><CleanerDashboard /></MemoryRouter>);
    expect(screen.getByText('Upcoming Schedule')).toBeInTheDocument();
  });
});
