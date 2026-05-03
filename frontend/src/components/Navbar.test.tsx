import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Navbar from './Navbar';
import * as storage from '../auth/storage';

// Mock the auth storage module
vi.mock('../auth/storage', () => ({
    getUser: vi.fn(),
    clearAuth: vi.fn(),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom');
    return { ...actual, useNavigate: () => mockNavigate };
});


const mockEndUser = {
    id: 1,
    email: "test@example.com",
    role: "end_user" as const,
    created_at: new Date().toISOString(),
};

const mockAdmin = {
    id: 2,
    email: "admin@example.com",
    role: "administrator" as const,
    created_at: new Date().toISOString(),
};

const mockCleaner = {
    id: 3,
    email: "cleaner@example.com",
    role: "cleaner" as const,
    created_at: new Date().toISOString(),
};

describe('Navbar', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('shows login/register when logged out', () => {
        vi.mocked(storage.getUser).mockReturnValue(null);
        render(<MemoryRouter><Navbar /></MemoryRouter>);

        expect(screen.getByText(/login/i)).toBeInTheDocument();
        expect(screen.getByText(/register/i)).toBeInTheDocument();
        expect(screen.queryByText(/logout/i)).not.toBeInTheDocument();
    });

    it('shows cleaner-specific links for cleaner role', () => {
        vi.mocked(storage.getUser).mockReturnValue(mockCleaner);
        render(<MemoryRouter><Navbar /></MemoryRouter>);

        expect(screen.getByText(/cleaner profile/i)).toBeInTheDocument();
        expect(screen.queryByText(/view cleaners/i)).not.toBeInTheDocument();
    });

    it('shows admin links for administrator role', () => {
        vi.mocked(storage.getUser).mockReturnValue(mockAdmin);
        render(<MemoryRouter><Navbar /></MemoryRouter>);

        expect(screen.getByText(/users/i)).toBeInTheDocument();
        expect(screen.getByText(/bookings/i)).toBeInTheDocument();
    });

    it('calls clearAuth and navigates on logout', async () => {
        vi.mocked(storage.getUser).mockReturnValue(mockEndUser);
        render(<MemoryRouter><Navbar /></MemoryRouter>);

        await userEvent.click(screen.getByText(/logout/i));

        expect(storage.clearAuth).toHaveBeenCalled();
        expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true });
    });
});