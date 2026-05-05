import { describe, it, expect, vi, afterEach } from 'vitest';
import { listCleaners } from './cleaners';

vi.mock('../auth/storage', () => ({
  getToken: vi.fn().mockReturnValue('user-token'),
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

const MOCK_CLEANER = {
  user_id: 1,
  email: 'cleaner@test.com',
  first_name: 'Alice',
  last_name: 'Smith',
  city: 'Singapore',
  cleaner_profile: { id: 10, user_id: 1, service_type: 'full', hourly_rate: 30, years_experience: 3 },
};

describe('cleaners API', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('listCleaners sends GET to /api/cleaner/list with stored token', async () => {
    const fetchMock = mockFetch(200, { cleaners: [] });
    await listCleaners();
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/cleaner/list');
    expect((opts.headers as Record<string, string>)['Authorization']).toBe('Bearer user-token');
  });

  it('listCleaners returns parsed cleaners array', async () => {
    mockFetch(200, { cleaners: [MOCK_CLEANER] });
    const result = await listCleaners();
    expect(result.cleaners).toHaveLength(1);
    expect(result.cleaners[0].first_name).toBe('Alice');
  });

  it('listCleaners returns empty array when no cleaners exist', async () => {
    mockFetch(200, { cleaners: [] });
    const result = await listCleaners();
    expect(result.cleaners).toHaveLength(0);
  });

  it('listCleaners uses GET method (no body)', async () => {
    const fetchMock = mockFetch(200, { cleaners: [] });
    await listCleaners();
    const [, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(opts.body).toBeUndefined();
  });

  it('listCleaners appends eligibility filters to the query string', async () => {
    const fetchMock = mockFetch(200, { cleaners: [] });

    await listCleaners({
      service_type: 'full',
      preferred_date: '2099-12-31',
      preferred_time_start: '10:00',
      preferred_time_end: '12:00',
      exclude_job_request_id: 42,
    });

    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    const requestUrl = new URL(url, 'http://localhost');
    expect(requestUrl.pathname).toBe('/api/cleaner/list');
    expect(requestUrl.searchParams.get('service_type')).toBe('full');
    expect(requestUrl.searchParams.get('preferred_date')).toBe('2099-12-31');
    expect(requestUrl.searchParams.get('preferred_time_start')).toBe('10:00');
    expect(requestUrl.searchParams.get('preferred_time_end')).toBe('12:00');
    expect(requestUrl.searchParams.get('exclude_job_request_id')).toBe('42');
  });

  it('listCleaners throws with server error message on failure', async () => {
    mockFetch(500, { message: 'Internal server error.' });
    await expect(listCleaners()).rejects.toThrow('Internal server error.');
  });
});
