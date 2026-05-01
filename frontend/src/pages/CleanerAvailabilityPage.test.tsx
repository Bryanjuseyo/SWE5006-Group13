import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import CleanerAvailabilityPage from './CleanerAvailabilityPage';
import * as availabilityApi from '../api/cleanerAvailability';

vi.mock('../api/cleanerAvailability', () => ({
  getAvailability: vi.fn(),
  addAvailability: vi.fn(),
  updateAvailability: vi.fn(),
  deleteAvailability: vi.fn(),
}));

vi.mock('../auth/storage', () => ({
  getUser: vi.fn().mockReturnValue({ id: 2, email: 'cleaner@test.com', role: 'cleaner', created_at: '' }),
  clearAuth: vi.fn(),
}));

const MOCK_SLOT: availabilityApi.AvailabilitySlot = {
  id: 1,
  cleaner_profile_id: 10,
  start_date: '2099-09-01',
  end_date: '2099-09-30',
  start_time: '09:00:00',
  end_time: '17:00:00',
};

describe('CleanerAvailabilityPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders the page heading', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [] });
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Availability Management')).toBeInTheDocument();
    });
  });

  it('renders availability slots after fetch', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [MOCK_SLOT] });
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText(/your availability slots/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no slots set', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [] });
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText(/no availability slots set/i)).toBeInTheDocument();
    });
  });

  it('shows error alert when fetch fails', async () => {
    vi.mocked(availabilityApi.getAvailability).mockRejectedValue(new Error('Failed to load availability.'));
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('Failed to load availability.')).toBeInTheDocument();
    });
  });

  it('renders the Add Slot button', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [] });
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /add slot/i })).toBeInTheDocument();
    });
  });
});

describe('CleanerAvailabilityPage – form submission', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls addAvailability and shows success message with valid dates', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [] });
    vi.mocked(availabilityApi.addAvailability).mockResolvedValue({ slot: MOCK_SLOT });
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /add slot/i }));

    const dateInputs = document.querySelectorAll('input[type="date"]');
    fireEvent.change(dateInputs[0], { target: { value: '2099-09-01' } });
    fireEvent.change(dateInputs[1], { target: { value: '2099-09-30' } });
    await userEvent.click(screen.getByRole('button', { name: /add slot/i }));

    await waitFor(() => {
      expect(availabilityApi.addAvailability).toHaveBeenCalledOnce();
    });
  });

  it('shows validation error when dates are missing', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [] });
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /add slot/i }));

    fireEvent.submit(document.querySelector('form')!);

    await waitFor(() => {
      expect(screen.getByText('Start date and end date are required.')).toBeInTheDocument();
    });
  });

  it('shows error when end date is before start date', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [] });
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /add slot/i }));

    const dateInputs = document.querySelectorAll('input[type="date"]');
    fireEvent.change(dateInputs[0], { target: { value: '2099-09-30' } });
    fireEvent.change(dateInputs[1], { target: { value: '2099-09-01' } });
    fireEvent.submit(document.querySelector('form')!);

    await waitFor(() => {
      expect(screen.getByText('End date must be on or after start date.')).toBeInTheDocument();
    });
  });

  it('shows error when end time is not after start time', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [] });
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /add slot/i }));

    const dateInputs = document.querySelectorAll('input[type="date"]');
    const timeInputs = document.querySelectorAll('input[type="time"]');
    fireEvent.change(dateInputs[0], { target: { value: '2099-09-01' } });
    fireEvent.change(dateInputs[1], { target: { value: '2099-09-30' } });
    fireEvent.change(timeInputs[0], { target: { value: '17:00' } });
    fireEvent.change(timeInputs[1], { target: { value: '09:00' } });
    fireEvent.submit(document.querySelector('form')!);

    await waitFor(() => {
      expect(screen.getByText('End time must be after start time.')).toBeInTheDocument();
    });
  });

  it('shows error message when addAvailability fails', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [] });
    vi.mocked(availabilityApi.addAvailability).mockRejectedValue(new Error('Failed to save availability slot.'));
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /add slot/i }));

    const dateInputs = document.querySelectorAll('input[type="date"]');
    fireEvent.change(dateInputs[0], { target: { value: '2099-09-01' } });
    fireEvent.change(dateInputs[1], { target: { value: '2099-09-30' } });
    await userEvent.click(screen.getByRole('button', { name: /add slot/i }));

    await waitFor(() => {
      expect(screen.getByText('Failed to save availability slot.')).toBeInTheDocument();
    });
  });
});

describe('CleanerAvailabilityPage – edit and delete', () => {
  beforeEach(() => vi.clearAllMocks());

  it('clicking Edit populates the form and shows "Edit Availability Slot" heading', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [MOCK_SLOT] });
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /^edit$/i }));

    await userEvent.click(screen.getByRole('button', { name: /^edit$/i }));

    await waitFor(() => {
      expect(screen.getByText('Edit Availability Slot')).toBeInTheDocument();
    });
  });

  it('submitting after Edit calls updateAvailability not addAvailability', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [MOCK_SLOT] });
    vi.mocked(availabilityApi.updateAvailability).mockResolvedValue({ slot: MOCK_SLOT });
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /^edit$/i }));

    await userEvent.click(screen.getByRole('button', { name: /^edit$/i }));
    await waitFor(() => screen.getByText('Edit Availability Slot'));

    await userEvent.click(screen.getByRole('button', { name: /save changes/i }));

    await waitFor(() => {
      expect(availabilityApi.updateAvailability).toHaveBeenCalledWith(MOCK_SLOT.id, expect.any(Object));
      expect(availabilityApi.addAvailability).not.toHaveBeenCalled();
    });
  });

  it('clicking Cancel when editing resets form to "Add Availability Slot"', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [MOCK_SLOT] });
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /^edit$/i }));

    await userEvent.click(screen.getByRole('button', { name: /^edit$/i }));
    await waitFor(() => screen.getByText('Edit Availability Slot'));

    await userEvent.click(screen.getByRole('button', { name: /cancel/i }));

    await waitFor(() => {
      expect(screen.getByText('Add Availability Slot')).toBeInTheDocument();
    });
  });

  it('clicking Remove calls deleteAvailability and removes slot from list', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [MOCK_SLOT] });
    vi.mocked(availabilityApi.deleteAvailability).mockResolvedValue(undefined);
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /remove/i }));

    await userEvent.click(screen.getByRole('button', { name: /remove/i }));

    await waitFor(() => {
      expect(availabilityApi.deleteAvailability).toHaveBeenCalledWith(MOCK_SLOT.id);
      expect(screen.getByText(/no availability slots set/i)).toBeInTheDocument();
    });
  });

  it('shows error message when deleteAvailability fails', async () => {
    vi.mocked(availabilityApi.getAvailability).mockResolvedValue({ availability: [MOCK_SLOT] });
    vi.mocked(availabilityApi.deleteAvailability).mockRejectedValue(new Error('Failed to remove slot.'));
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    render(<MemoryRouter><CleanerAvailabilityPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole('button', { name: /remove/i }));

    await userEvent.click(screen.getByRole('button', { name: /remove/i }));

    await waitFor(() => {
      expect(screen.getByText('Failed to remove slot.')).toBeInTheDocument();
    });
  });
});
