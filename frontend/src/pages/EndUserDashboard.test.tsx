import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import EndUserDashboard from './EndUserDashboard';

vi.mock('../auth/storage', () => ({
  getUser: vi.fn().mockReturnValue({
    id: 1, email: 'user@test.com', role: 'end_user', created_at: '',
  }),
  getToken: vi.fn().mockReturnValue('test-token'),
  clearAuth: vi.fn(),
}));

vi.mock('../components/JobRequestList', () => ({
  default: () => <div data-testid="job-request-list">Job Request List</div>,
}));

describe('EndUserDashboard', () => {
  it('renders the End-User Dashboard heading', () => {
    render(<MemoryRouter><EndUserDashboard /></MemoryRouter>);
    expect(screen.getByText('End-User Dashboard')).toBeInTheDocument();
  });

  it('renders the JobRequestList component', () => {
    render(<MemoryRouter><EndUserDashboard /></MemoryRouter>);
    expect(screen.getByTestId('job-request-list')).toBeInTheDocument();
  });

  it('contains a main element', () => {
    render(<MemoryRouter><EndUserDashboard /></MemoryRouter>);
    expect(document.querySelector('main')).toBeInTheDocument();
  });

  it('renders without crashing', () => {
    const { container } = render(<MemoryRouter><EndUserDashboard /></MemoryRouter>);
    expect(container).toBeTruthy();
  });

  it('renders heading with h1 tag', () => {
    render(<MemoryRouter><EndUserDashboard /></MemoryRouter>);
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
  });
});
