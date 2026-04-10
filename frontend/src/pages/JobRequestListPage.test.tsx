import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import JobRequestListPage from './JobRequestListPage';

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

describe('JobRequestListPage', () => {
  it('renders the JobRequestList component', () => {
    render(<MemoryRouter><JobRequestListPage /></MemoryRouter>);
    expect(screen.getByTestId('job-request-list')).toBeInTheDocument();
  });

  it('renders without crashing', () => {
    const { container } = render(<MemoryRouter><JobRequestListPage /></MemoryRouter>);
    expect(container).toBeTruthy();
  });

  it('contains a main element', () => {
    render(<MemoryRouter><JobRequestListPage /></MemoryRouter>);
    expect(document.querySelector('main')).toBeInTheDocument();
  });

  it('renders a container with padding', () => {
    render(<MemoryRouter><JobRequestListPage /></MemoryRouter>);
    const main = document.querySelector('main');
    expect(main?.className).toContain('container');
  });

  it('displays the job request list content', () => {
    render(<MemoryRouter><JobRequestListPage /></MemoryRouter>);
    expect(screen.getByText('Job Request List')).toBeInTheDocument();
  });
});
