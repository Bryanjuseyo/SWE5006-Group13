import { useEffect, useState, useCallback } from 'react';
import Navbar from '../components/Navbar';
import { getToken } from '../auth/storage';
import {
  getCleanerSchedule,
  updateJobStatus,
  type JobRequest,
  type JobStatus,
  type PaginationMeta,
} from '../api/job_requests';

const STATUS_LABELS: Record<JobStatus, string> = {
  pending: 'Pending',
  confirmed: 'Confirmed',
  in_progress: 'In Progress',
  cleaner_completed: 'Awaiting End User Confirmation',
  completed: 'Completed',
  cancelled: 'Cancelled',
  rejected: 'Rejected',
};

const STATUS_COLORS: Record<JobStatus, string> = {
  pending: 'warning',
  confirmed: 'info',
  in_progress: 'primary',
  cleaner_completed: 'warning',
  completed: 'success',
  cancelled: 'secondary',
  rejected: 'danger',
};

function formatDate(d: string) {
  return new Date(d + 'T00:00:00').toLocaleDateString(undefined, {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
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

export default function CleanerSchedulePage() {
  const JOBS_PER_PAGE = 25;
  const token = getToken();
  const [schedule, setSchedule] = useState<JobRequest[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getCleanerSchedule(token!, page, JOBS_PER_PAGE);
      setSchedule(res.schedule);
      setPagination(res.pagination);
    } catch (e: unknown) {
      setError(getErrorMessage(e, 'Failed to load schedule.'));
    } finally {
      setLoading(false);
    }
  }, [token, page]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleStatusChange(id: number, newStatus: JobStatus) {
    try {
      const res = await updateJobStatus(id, newStatus, token!);
      setSchedule((prev) =>
        prev
          .map((j) => (j.id === id ? res.job_request : j))
          .filter((j) => j.status === 'confirmed' || j.status === 'in_progress')
      );
    } catch (e: unknown) {
      alert(getErrorMessage(e, 'Failed to update status.'));
    }
  }

  async function handleCancel(id: number) {
    if (!confirm('Cancel this job? The client will be notified.')) return;

    try {
      const res = await updateJobStatus(id, 'cancelled', token!);
      setSchedule((prev) => prev.filter((j) => j.id !== res.job_request.id));
    } catch (e: unknown) {
      alert(getErrorMessage(e, 'Failed to cancel job.'));
    }
  }

  return (
    <>
      <Navbar />
      <main className="container py-5" style={{ maxWidth: 860 }}>
        <h1 className="h3 fw-bold mb-1">Upcoming Schedule</h1>
        <p className="text-muted mb-4">Your confirmed and in-progress jobs coming up.</p>

        {error && <div className="alert alert-danger">{error}</div>}

        {loading ? (
          <div className="text-center py-5">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
          </div>
        ) : schedule.length === 0 ? (
          <div className="alert alert-info">
            No upcoming jobs scheduled. Accept some jobs to get started.
          </div>
        ) : (
          <>
          <div className="d-flex flex-column gap-3">
            {schedule.map((job) => (
              <div key={job.id} className="card shadow-sm">
                <div className="card-body">
                  <div className="d-flex justify-content-between align-items-start mb-2">
                    <div>
                      <h5 className="card-title mb-1">{job.title}</h5>
                      <span className={`badge bg-${STATUS_COLORS[job.status]}`}>
                        {STATUS_LABELS[job.status]}
                      </span>
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

                    <div className="col-auto">
                      <small className="text-muted">Service:</small>{' '}
                      <span className="text-capitalize">{job.service_type}</span>
                    </div>
                  </div>

                  {job.end_user && (
                    <div className="mt-2">
                      <small className="text-muted">Client:</small>{' '}
                      <span>{job.end_user.email}</span>
                    </div>
                  )}

                  <div className="mt-3 d-flex gap-2 flex-wrap">
                    {job.status === 'confirmed' && (
                      <>
                        <button
                          className="btn btn-sm btn-primary"
                          onClick={() => handleStatusChange(job.id, 'in_progress')}
                        >
                          Start Job
                        </button>
                        <button
                          className="btn btn-sm btn-outline-danger"
                          onClick={() => handleCancel(job.id)}
                        >
                          Cancel Job
                        </button>
                      </>
                    )}

                    {job.status === 'in_progress' && (
                      <button
                        className="btn btn-sm btn-success"
                        onClick={() => handleStatusChange(job.id, 'cleaner_completed')}
                      >
                        Mark Complete
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
          {pagination && (
            <div className="d-flex flex-column flex-md-row justify-content-between align-items-center gap-3 mt-4">
              <div className="text-muted small">
                Showing {(pagination.page - 1) * pagination.per_page + 1}-
                {Math.min(pagination.page * pagination.per_page, pagination.total)} of{' '}
                {pagination.total} scheduled jobs
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
