import { describe, it, expect, vi, afterEach } from 'vitest';
import { register, login, verify2FA, setup2FA, enable2FA, disable2FA, get2FAStatus } from './auth';

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

describe('auth API', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('register sends POST to /api/auth/register with user data', async () => {
    const fetchMock = mockFetch(200, { message: 'ok' });
    await register({ email: 'a@b.com', password: 'Pass1', role: 'end_user', first_name: 'A', last_name: 'B' });
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/auth/register');
    expect(opts.method).toBe('POST');
    expect(opts.body).toContain('a@b.com');
  });

  it('login sends POST to /api/auth/login with credentials', async () => {
    const fetchMock = mockFetch(200, { token: 'jwt', user: {} });
    await login({ email: 'u@test.com', password: 'secret' });
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/auth/login');
    expect(opts.method).toBe('POST');
    expect(opts.body).toContain('u@test.com');
  });

  it('verify2FA sends POST to /api/auth/2fa/verify with temp_token and otp', async () => {
    const fetchMock = mockFetch(200, { token: 'jwt' });
    await verify2FA({ temp_token: 'tmp', otp: '123456' });
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/auth/2fa/verify');
    expect(opts.method).toBe('POST');
    expect(opts.body).toContain('123456');
  });

  it('setup2FA sends POST to /api/auth/2fa/setup with Bearer token', async () => {
    const fetchMock = mockFetch(200, { message: 'OTP sent.' });
    await setup2FA('my-token');
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/auth/2fa/setup');
    expect((opts.headers as Record<string, string>)['Authorization']).toBe('Bearer my-token');
  });

  it('enable2FA sends POST to /api/auth/2fa/enable with otp in body', async () => {
    const fetchMock = mockFetch(200, { message: '2FA enabled.' });
    await enable2FA('654321', 'my-token');
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/auth/2fa/enable');
    expect(opts.body).toContain('654321');
  });

  it('disable2FA sends POST to /api/auth/2fa/disable with password in body', async () => {
    const fetchMock = mockFetch(200, { message: '2FA disabled.' });
    await disable2FA('mypassword', 'my-token');
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/auth/2fa/disable');
    expect(opts.body).toContain('mypassword');
  });

  it('get2FAStatus sends GET to /api/auth/2fa/status with Bearer token', async () => {
    const fetchMock = mockFetch(200, { two_factor_enabled: true });
    const result = await get2FAStatus('my-token');
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/auth/2fa/status');
    expect((opts.headers as Record<string, string>)['Authorization']).toBe('Bearer my-token');
    expect(result).toEqual({ two_factor_enabled: true });
  });

  it('login throws with server error message on non-ok response', async () => {
    mockFetch(401, { message: 'Invalid credentials.' });
    await expect(login({ email: 'x@x.com', password: 'bad' })).rejects.toThrow('Invalid credentials.');
  });
});
