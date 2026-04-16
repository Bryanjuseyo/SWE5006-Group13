import { describe, it, expect, vi, afterEach } from 'vitest';
import { getMyProfile, updateMyProfile } from './profile';

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

describe('profile API', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('getMyProfile sends GET to /api/profile with stored token', async () => {
    const fetchMock = mockFetch(200, { email: 'u@test.com', role: 'end_user', created_at: '', profile: null });
    await getMyProfile();
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/profile');
    expect((opts.headers as Record<string, string>)['Authorization']).toBe('Bearer user-token');
  });

  it('getMyProfile returns parsed profile response', async () => {
    mockFetch(200, { email: 'u@test.com', role: 'end_user', created_at: '2024-01-01', profile: null });
    const result = await getMyProfile();
    expect(result.email).toBe('u@test.com');
    expect(result.role).toBe('end_user');
  });

  it('updateMyProfile sends PUT to /api/profile with profile fields in body', async () => {
    const fetchMock = mockFetch(200, { message: 'saved', profile: {} });
    await updateMyProfile({ first_name: 'Jane', last_name: 'Doe' });
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/profile');
    expect(opts.method).toBe('PUT');
    expect(opts.body).toContain('Jane');
    expect(opts.body).toContain('Doe');
  });

  it('updateMyProfile includes optional phone and city fields', async () => {
    const fetchMock = mockFetch(200, { message: 'ok', profile: {} });
    await updateMyProfile({ first_name: 'A', last_name: 'B', phone: '91234567', city: 'Singapore' });
    const [, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(opts.body).toContain('91234567');
    expect(opts.body).toContain('Singapore');
  });

  it('getMyProfile throws with server error message on non-ok response', async () => {
    mockFetch(401, { message: 'Token expired.' });
    await expect(getMyProfile()).rejects.toThrow('Token expired.');
  });
});
