import { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import { getToken } from '../auth/storage';
import { getCleanerSchedule, updateJobStatus, type JobRequest, type JobStatus } from '../api/job_requests';

const STATUS_LABELS: Record<JobStatus, string> = {
  pending: 'Pending',
  confirmed: 'Confirmed',
  in_progress: 'In Progress',
  completed: 'Completed',
  cancelled: 'Cancelled',
  rejected: 'rejected',
};

const STATUS_COLORS: Record<JobStatus, string> = {
  pending: 'warning',
  confirmed: 'info',
  in_progress: 'primary',
  completed: 'success',
  cancelled: 'secondary',
  rejected: 'rejected',
};

function formatDate(d: string) {
  return new Date(d + 'T00:00:00').toLocaleDateString(undefined, {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  });
}

function formatTime(t: string | null) {
  if (!t) return null;
  const [h, m] = t.split(':');
  const date = new Date();
  date.setHours(Number(h), Number(m));
  return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

export default function CleanerSchedulePage() {
  const token = getToken();
  const [schedule, setSchedule] = useState<JobRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await getCleanerSchedule(token!);
      setSchedule(res.schedule);
    } catch (e: any) {
      setError(e?.message || 'Failed to load schedule.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleStatusChange(id: number, newStatus: JobStatus) {
    try {
      const res = await updateJobStatus(id, newStatus, token!);
      setSchedule((prev) => prev.map((j) => (j.id === id ? res.job_request : j))
        .filter((j) => ['confirmed', 'in_progress'].includes(j.status)));
    } catch (e: any) {
      alert(e?.message || 'Failed to update status.');
    }
  }

  async function handleCancel(id: number) {
    if (!confirm('Cancel this job? The client will be notified.')) return;
    try {
      const res = await updateJobStatus(id, 'cancelled', token!);
      setSchedule((prev) => prev.filter((j) => j.id !== res.job_request.id));
    } catch (e: any) {
      alert(e?.message || 'Failed to cancel job.');
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
          <div className="alert alert-info">No upcoming jobs scheduled. Accept some jobs to get started.</div>
        ) : (
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

                  {job.description && (
                    <p className="text-muted small mb-2">{job.description}</p>
                  )}

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
                        onClick={() => handleStatusChange(job.id, 'completed')}
                      >
                        Mark Complete
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </>
  );
}
