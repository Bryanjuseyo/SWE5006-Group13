import { describe, it, expect, vi, afterEach } from 'vitest';
import { getAvailability, addAvailability, updateAvailability, deleteAvailability } from './cleanerAvailability';

vi.mock('../auth/storage', () => ({
  getToken: vi.fn().mockReturnValue('cleaner-token'),
}));

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

describe('cleanerAvailability API', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('getAvailability sends GET to /api/cleaner/availability with stored token', async () => {
    const fetchMock = mockFetch(200, { availability: [] });
    await getAvailability();
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/cleaner/availability');
    expect((opts.headers as Record<string, string>)['Authorization']).toBe('Bearer cleaner-token');
  });

  it('addAvailability sends POST with start_date and end_date in body', async () => {
    const fetchMock = mockFetch(200, { message: 'added', availability: {} });
    await addAvailability({ start_date: '2099-01-01', end_date: '2099-01-31' });
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/cleaner/availability');
    expect(opts.method).toBe('POST');
    expect(opts.body).toContain('2099-01-01');
  });

  it('updateAvailability sends PUT to /api/cleaner/availability/:id', async () => {
    const fetchMock = mockFetch(200, { message: 'updated', availability: {} });
    await updateAvailability(4, { start_date: '2099-02-01', end_date: '2099-02-28' });
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/cleaner/availability/4');
    expect(opts.method).toBe('PUT');
  });

  it('deleteAvailability sends DELETE to /api/cleaner/availability/:id', async () => {
    const fetchMock = mockFetch(200, { message: 'deleted' });
    await deleteAvailability(7);
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/cleaner/availability/7');
    expect(opts.method).toBe('DELETE');
  });

  it('getAvailability throws with server error message on failure', async () => {
    mockFetch(403, { message: 'Forbidden.' });
    await expect(getAvailability()).rejects.toThrow('Forbidden.');
  });
});
