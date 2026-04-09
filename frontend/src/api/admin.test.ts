import { describe, it, expect, vi, afterEach } from 'vitest';
import {
  getAdminStats,
  getAdminUsers,
  banUser,
  unbanUser,
  getAdminBookings,
  rejectBooking,
  autoAssignCleaner,
} from './admin';

function mockFetch(status: number, data: unknown) {
  const fn = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    headers: { get: (_: string) => 'application/json' },
    json: async () => data,
  });
  vi.stubGlobal('fetch', fn);
  return fn;
}

describe('admin API', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('getAdminStats sends GET to /api/admin/stats with Bearer token', async () => {
    const fetchMock = mockFetch(200, { users: {}, jobs: {} });
    await getAdminStats('admin-token');
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/admin/stats');
    expect((opts.headers as Record<string, string>)['Authorization']).toBe('Bearer admin-token');
  });

  it('getAdminUsers appends role and search query params when provided', async () => {
    const fetchMock = mockFetch(200, { users: [] });
    await getAdminUsers('tok', { role: 'cleaner', search: 'alice' });
    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('role=cleaner');
    expect(url).toContain('search=alice');
  });

  it('getAdminUsers calls /api/admin/users without query when no params', async () => {
    const fetchMock = mockFetch(200, { users: [] });
    await getAdminUsers('tok');
    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/api\/admin\/users$/);
  });

  it('banUser sends PATCH to /api/admin/users/:id/ban with reason', async () => {
    const fetchMock = mockFetch(200, { message: 'banned', user: {} });
    await banUser(5, 'tok', 'spam');
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/admin/users/5/ban');
    expect(opts.method).toBe('PATCH');
    expect(opts.body).toContain('spam');
  });

  it('unbanUser sends PATCH to /api/admin/users/:id/unban', async () => {
    const fetchMock = mockFetch(200, { message: 'unbanned', user: {} });
    await unbanUser(7, 'tok');
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/admin/users/7/unban');
    expect(opts.method).toBe('PATCH');
  });

  it('getAdminBookings appends status filter when provided', async () => {
    const fetchMock = mockFetch(200, { job_requests: [] });
    await getAdminBookings('tok', { status: 'pending' });
    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('status=pending');
  });

  it('rejectBooking sends PATCH to /api/admin/bookings/:id/reject', async () => {
    const fetchMock = mockFetch(200, { message: 'rejected', job_request: {} });
    await rejectBooking(3, 'tok');
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/admin/bookings/3/reject');
    expect(opts.method).toBe('PATCH');
  });

  it('autoAssignCleaner sends POST to /api/job-requests/:id/auto-assign', async () => {
    const fetchMock = mockFetch(200, { message: 'assigned', job_request: {}, assigned_cleaner: {} });
    await autoAssignCleaner(9, 'tok');
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/job-requests/9/auto-assign');
    expect(opts.method).toBe('POST');
  });
});
