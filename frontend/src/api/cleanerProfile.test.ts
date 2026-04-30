import { describe, it, expect, vi, afterEach } from 'vitest';
import { getCleanerProfile, updateCleanerProfile } from './cleanerProfile';

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

describe('cleanerProfile API', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('getCleanerProfile sends GET to /api/cleaner/profile with stored token', async () => {
    const fetchMock = mockFetch(200, { profile: null });
    const result = await getCleanerProfile();
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/cleaner/profile');
    expect((opts.headers as Record<string, string>)['Authorization']).toBe('Bearer cleaner-token');
    expect(result).toEqual({ profile: null });
  });

  it('getCleanerProfile returns profile data on success', async () => {
    mockFetch(200, { profile: { id: 1, user_id: 2, service_type: 'full', years_experience: 3 } });
    const result = await getCleanerProfile();
    expect(result.profile?.service_type).toBe('full');
  });

  it('updateCleanerProfile sends PUT to /api/cleaner/profile with body', async () => {
    const fetchMock = mockFetch(200, { message: 'updated', profile: {} });
    await updateCleanerProfile({ service_type: 'partial', hourly_rate: 20, years_experience: 2 });
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/cleaner/profile');
    expect(opts.method).toBe('PUT');
    expect(opts.body).toContain('partial');
  });

  it('updateCleanerProfile includes hourly_rate in request body', async () => {
    const fetchMock = mockFetch(200, { message: 'ok', profile: {} });
    await updateCleanerProfile({ hourly_rate: 35.5 });
    const [, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(opts.body).toContain('35.5');
  });

  it('getCleanerProfile throws on non-ok response', async () => {
    mockFetch(401, { message: 'Unauthorized.' });
    await expect(getCleanerProfile()).rejects.toThrow('Unauthorized.');
  });
});
