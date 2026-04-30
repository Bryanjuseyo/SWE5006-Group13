/**
 * Service logic tests — src/api/client.ts
 *
 * Tests cover: apiRequest — URL construction, headers, body serialisation,
 * success/error response handling.
 */
import { describe, it, expect, vi, afterEach } from 'vitest';
import { apiRequest } from './client';

/** Helper: stub globalThis.fetch with a resolved response. */
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

describe('apiRequest', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('calls fetch with the correct path and returns parsed JSON on success', async () => {
    const fetchMock = mockFetch(200, { status: 'ok' });

    const result = await apiRequest<{ status: string }>('/api/health');

    expect(fetchMock).toHaveBeenCalledOnce();
    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/health');
    expect(result).toEqual({ status: 'ok' });
  });

  it('includes Authorization Bearer header when a token is supplied', async () => {
    const fetchMock = mockFetch(200, {});

    await apiRequest('/api/profile', { token: 'my-token' });

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect((options.headers as Record<string, string>)['Authorization']).toBe('Bearer my-token');
  });

  it('omits Authorization header when token is null', async () => {
    const fetchMock = mockFetch(200, {});

    await apiRequest('/api/health', { token: null });

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect((options.headers as Record<string, string>)['Authorization']).toBeUndefined();
  });

  it('throws an Error with the message from the response body on a non-ok response', async () => {
    mockFetch(401, { message: 'Invalid email or password.' });

    await expect(
      apiRequest('/api/auth/login', { method: 'POST', body: { email: 'x@x.com' } })
    ).rejects.toThrow('Invalid email or password.');
  });

  it('sends a POST request with a JSON-serialised body', async () => {
    const fetchMock = mockFetch(200, { token: 'abc' });

    await apiRequest('/api/auth/login', {
      method: 'POST',
      body: { email: 'a@b.com', password: 'pass' },
    });

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(options.method).toBe('POST');
    expect(options.body).toBe(JSON.stringify({ email: 'a@b.com', password: 'pass' }));
  });
});
