import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  getJobRequests,
  deleteJobRequest,
  updateJobStatus,
  type JobRequest,
  type JobStatus,
} from '../api/job_requests';
import { getToken, getUser } from '../auth/storage';

const STATUS_LABELS: Record<JobStatus, string> = {
  pending: 'Pending',
  confirmed: 'Confirmed',
  in_progress: 'In Progress',
  completed: 'Completed',
  cancelled: 'Cancelled',
};

const STATUS_COLORS: Record<JobStatus, string> = {
  pending: 'warning',
  confirmed: 'info',
  in_progress: 'primary',
  completed: 'success',
  cancelled: 'secondary',
};

export default function JobRequestList() {
  const token = getToken();
  const user = getUser();

  const [jobRequests, setJobRequests] = useState<JobRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<JobStatus | ''>('');

  const isEndUser = user?.role === 'end_user';
  const isCleaner = user?.role === 'cleaner';

  useEffect(() => {
    fetchJobRequests();
  }, [statusFilter]);

  async function fetchJobRequests() {
    try {
      setLoading(true);
      setError(null);
      const res = await getJobRequests(token!, statusFilter || undefined);
      setJobRequests(res.job_requests);
    } catch (err: any) {
      setError(err?.message || 'Failed to load job requests.');
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Are you sure you want to delete this job request?')) return;
    try {
      await deleteJobRequest(id, token!);
      setJobRequests((prev) => prev.filter((j) => j.id !== id));
    } catch (err: any) {
      alert(err?.message || 'Failed to delete job request.');
    }
  }

  async function handleCancel(id: number) {
    if (!confirm('Are you sure you want to cancel this job request?')) return;
    try {
      const res = await updateJobStatus(id, 'cancelled', token!);
      setJobRequests((prev) => prev.map((j) => (j.id === id ? res.job_request : j)));
    } catch (err: any) {
      alert(err?.message || 'Failed to cancel job request.');
    }
  }

  async function handleStatusChange(id: number, newStatus: JobStatus) {
    try {
      const res = await updateJobStatus(id, newStatus, token!);
      setJobRequests((prev) => prev.map((j) => (j.id === id ? res.job_request : j)));
    } catch (err: any) {
      alert(err?.message || 'Failed to update status.');
    }
  }

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2 className="h4 fw-bold mb-0">Job Requests</h2>
        {isEndUser && (
          <Link to="/job-requests/new" className="btn btn-primary btn-sm">
            + New Job Request
          </Link>
        )}
      </div>

      <div className="mb-4">
        <label className="form-label">Filter by Status:</label>
        <select
          className="form-select"
          style={{ maxWidth: 200 }}
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as JobStatus | '')}
        >
          <option value="">All</option>
          <option value="pending">Pending</option>
          <option value="confirmed">Confirmed</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {loading ? (
        <div className="text-center py-5">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      ) : jobRequests.length === 0 ? (
        <div className="alert alert-info">
          {statusFilter ? (
            `No job requests with status "${STATUS_LABELS[statusFilter as JobStatus]}" found.`
          ) : (
            <>
              No job requests found.
              {isEndUser && (
                <> <Link to="/job-requests/new">Create your first job request</Link>.</>
              )}
            </>
          )}
        </div>
      ) : (
        <div className="row g-3">
          {jobRequests.map((job) => (
            <div key={job.id} className="col-12">
              <div className="card shadow-sm">
                <div className="card-body">
                  <div className="d-flex justify-content-between align-items-start">
                    <div>
                      <h5 className="card-title mb-1">{job.title}</h5>
                      <span className={`badge bg-${STATUS_COLORS[job.status]}`}>
                        {STATUS_LABELS[job.status]}
                      </span>
                    </div>
                    <small className="text-muted">#{job.id}</small>
                  </div>

                  {job.description && (
                    <p className="card-text text-muted mt-2 mb-2">{job.description}</p>
                  )}

                  <div className="row mt-3">
                    {job.preferred_date && (
                      <div className="col-auto">
                        <small className="text-muted">Date:</small>{' '}
                        <span>{job.preferred_date}</span>
                      </div>
                    )}
                    {job.preferred_time_start && (
                      <div className="col-auto">
                        <small className="text-muted">Time:</small>{' '}
                        <span>
                          {job.preferred_time_start}
                          {job.preferred_time_end && ` - ${job.preferred_time_end}`}
                        </span>
                      </div>
                    )}
                    {job.location && (
                      <div className="col-auto">
                        <small className="text-muted">Location:</small>{' '}
                        <span>{job.location}</span>
                      </div>
                    )}
                    {job.service_type && (
                      <div className="col-auto">
                        <small className="text-muted">Service:</small>{' '}
                        <span className="text-capitalize">{job.service_type}</span>
                      </div>
                    )}
                  </div>

                  {job.cleaner && (
                    <div className="mt-2">
                      <small className="text-muted">Cleaner:</small>{' '}
                      <span>{job.cleaner.email}</span>
                    </div>
                  )}

                  <div className="mt-3 d-flex gap-2 flex-wrap">
                    <Link to={`/job-requests/${job.id}`} className="btn btn-sm btn-primary">
                      View Details
                    </Link>

                    {isEndUser && job.status === 'pending' && (
                      <>
                        <Link
                          to={`/job-requests/${job.id}/edit`}
                          className="btn btn-sm btn-secondary"
                        >
                          Edit
                        </Link>
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() => handleDelete(job.id)}
                        >
                          Delete
                        </button>
                      </>
                    )}

                    {isEndUser &&
                      job.cleaner_id !== null &&
                      ['pending', 'confirmed'].includes(job.status) && (
                        <button
                          className="btn btn-sm btn-warning"
                          onClick={() => handleCancel(job.id)}
                        >
                          Cancel
                        </button>
                      )}

                    {isCleaner && job.status === 'pending' && (
                      <button
                        className="btn btn-sm btn-success"
                        onClick={() => handleStatusChange(job.id, 'confirmed')}
                      >
                        Accept Job
                      </button>
                    )}

                    {isCleaner && job.status === 'confirmed' && (
                      <button
                        className="btn btn-sm btn-primary"
                        onClick={() => handleStatusChange(job.id, 'in_progress')}
                      >
                        Start Job
                      </button>
                    )}

                    {isCleaner && job.status === 'in_progress' && (
                      <button
                        className="btn btn-sm btn-success"
                        onClick={() => handleStatusChange(job.id, 'completed')}
                      >
                        Complete Job
                      </button>
                    )}
                  </div>
                </div>
                <div className="card-footer text-muted small">
                  Created: {new Date(job.created_at).toLocaleString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
