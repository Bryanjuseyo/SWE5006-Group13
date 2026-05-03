import { describe, it, expect, vi, afterEach } from 'vitest';
import {
  getJobRequests,
  getJobRequest,
  createJobRequest,
  deleteJobRequest,
  updateJobStatus,
  getAvailableJobs,
  getCleanerSchedule,
} from './job_requests';

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

describe('job_requests API', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('getJobRequests sends GET to /api/job-requests with Bearer token', async () => {
    const fetchMock = mockFetch(200, { job_requests: [] });
    await getJobRequests('my-token');
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/job-requests');
    expect((opts.headers as Record<string, string>)['Authorization']).toBe('Bearer my-token');
  });

  it('getJobRequest sends GET to /api/job-requests/:id', async () => {
    const fetchMock = mockFetch(200, { job_request: { id: 42 } });
    await getJobRequest(42, 'tok');
    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/job-requests/42');
  });

  it('createJobRequest sends POST with job data in body', async () => {
    const fetchMock = mockFetch(200, { job_request: {} });
    await createJobRequest(
      { title: 'Deep Clean', service_type: 'full', location: '1 Orchard', preferred_date: '2099-08-01' },
      'tok'
    );
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/job-requests');
    expect(opts.method).toBe('POST');
    expect(opts.body).toContain('Deep Clean');
  });

  it('deleteJobRequest sends DELETE to /api/job-requests/:id', async () => {
    const fetchMock = mockFetch(200, { message: 'deleted' });
    await deleteJobRequest(5, 'tok');
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/job-requests/5');
    expect(opts.method).toBe('DELETE');
  });

  it('updateJobStatus sends PATCH to /api/job-requests/:id/status with new status', async () => {
    const fetchMock = mockFetch(200, { job_request: { id: 3, status: 'confirmed' } });
    await updateJobStatus(3, 'confirmed', 'tok');
    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/job-requests/3/status');
    expect(opts.method).toBe('PATCH');
    expect(opts.body).toContain('confirmed');
  });

  it('getAvailableJobs sends GET to /api/job-requests/available', async () => {
    const fetchMock = mockFetch(200, { job_requests: [] });
    await getAvailableJobs('tok');
    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/available');
  });

  it('getCleanerSchedule sends GET to /api/cleaner/schedule', async () => {
    const fetchMock = mockFetch(200, { schedule: [] });
    await getCleanerSchedule('tok');
    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/cleaner/schedule');
  });

  it('getJobRequests throws with error message on non-ok response', async () => {
    mockFetch(403, { message: 'Access denied.' });
    await expect(getJobRequests('bad-token')).rejects.toThrow('Access denied.');
  });
});
