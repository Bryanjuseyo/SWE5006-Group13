import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { getToken, getUser } from '../auth/storage';
import {
  getAvailableJobs,
  updateJobStatus,
  type JobRequest,
  type PaginationMeta,
} from '../api/job_requests';

function formatDate(d: string) {
  return new Date(d + 'T00:00:00').toLocaleDateString(undefined, {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatTime(t: string | null) {
  if (!t) return null;
  const [h, m] = t.split(':');
  const date = new Date();
  date.setHours(Number(h), Number(m));
  return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export default function BrowseJobsPage() {
  const JOBS_PER_PAGE = 25;
  const token = getToken();
  const currentUser = getUser();
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<JobRequest[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [accepting, setAccepting] = useState<number | null>(null);
  const [page, setPage] = useState(1);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getAvailableJobs(token!, page, JOBS_PER_PAGE);
      setJobs(res.job_requests);
      setPagination(res.pagination);
    } catch (e: unknown) {
      setError(getErrorMessage(e, 'Failed to load available jobs.'));
    } finally {
      setLoading(false);
    }
  }, [token, page]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleAccept(id: number) {
    setAccepting(id);
    try {
      await updateJobStatus(id, 'confirmed', token!);
      setJobs((prev) => prev.filter((j) => j.id !== id));
      navigate('/cleaner/schedule');
    } catch (e: unknown) {
      alert(getErrorMessage(e, 'Failed to accept job.'));
      setAccepting(null);
    }
  }

  return (
    <>
      <Navbar />
      <main className="container py-5" style={{ maxWidth: 860 }}>
        <h1 className="h3 fw-bold mb-1">Available Jobs</h1>
        <p className="text-muted mb-4">
          Open job requests matching your service type. Accept jobs that fit your schedule.
        </p>

        {error && <div className="alert alert-danger">{error}</div>}

        {loading ? (
          <div className="text-center py-5">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
          </div>
        ) : jobs.length === 0 ? (
          <div className="alert alert-info">
            No available jobs matching your service type right now. Check back later.
          </div>
        ) : (
          <>
          <div className="d-flex flex-column gap-3">
            {jobs.map((job) => (
              <div key={job.id} className="card shadow-sm">
                <div className="card-body">
                  <div className="d-flex justify-content-between align-items-start mb-2">
                    <div>
                      <h5 className="card-title mb-1">{job.title}</h5>
                      <span className="badge bg-warning text-dark">Pending</span>
                      <span className="badge bg-light text-dark border ms-1 text-capitalize">
                        {job.service_type}
                      </span>
                      {job.cleaner_id === currentUser?.id && (
                        <span className="badge bg-success ms-1">Preferred</span>
                      )}
                    </div>
                    <small className="text-muted">#{job.id}</small>
                  </div>

                  {job.description && <p className="text-muted small mb-2">{job.description}</p>}

                  <div className="row g-2 mt-1">
                    <div className="col-auto">
                      <small className="text-muted">Date:</small>{' '}
                      <strong>{formatDate(job.preferred_date!)}</strong>
                    </div>
                    {job.preferred_time_start && (
                      <div className="col-auto">
                        <small className="text-muted">Time:</small>{' '}
                        <strong>
                          {formatTime(job.preferred_time_start)}
                          {job.preferred_time_end && ` - ${formatTime(job.preferred_time_end)}`}
                        </strong>
                      </div>
                    )}
                    <div className="col-auto">
                      <small className="text-muted">Location:</small>{' '}
                      <span>{job.location}</span>
                    </div>
                  </div>

                  <div className="mt-3">
                    <button
                      className="btn btn-success btn-sm"
                      disabled={accepting === job.id}
                      onClick={() => handleAccept(job.id)}
                    >
                      {accepting === job.id ? 'Accepting...' : 'Accept Job'}
                    </button>
                  </div>
                </div>
                <div className="card-footer text-muted small">
                  Posted: {new Date(job.created_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
          {pagination && (
            <div className="d-flex flex-column flex-md-row justify-content-between align-items-center gap-3 mt-4">
              <div className="text-muted small">
                Showing {(pagination.page - 1) * pagination.per_page + 1}-
                {Math.min(pagination.page * pagination.per_page, pagination.total)} of{' '}
                {pagination.total} available jobs
              </div>
              <div className="d-flex align-items-center gap-2">
                <button
                  className="btn btn-sm btn-outline-secondary"
                  disabled={!pagination.has_prev}
                  onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                >
                  Previous
                </button>
                <span className="small text-muted">
                  Page {pagination.page} of {Math.max(pagination.total_pages, 1)}
                </span>
                <button
                  className="btn btn-sm btn-outline-secondary"
                  disabled={!pagination.has_next}
                  onClick={() => setPage((prev) => prev + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          )}
          </>
        )}
      </main>
    </>
  );
}
