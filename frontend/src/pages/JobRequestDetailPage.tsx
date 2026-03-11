import { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import {
  getJobRequest,
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

export default function JobRequestDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const [jobRequest, setJobRequest] = useState<JobRequest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const token = getToken();
  const user = getUser();

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }
    fetchJobRequest();
  }, [token, id]);

  async function fetchJobRequest() {
    try {
      setLoading(true);
      setError(null);
      const res = await getJobRequest(Number(id), token!);
      setJobRequest(res.job_request);
    } catch (err: any) {
      setError(err?.message || 'Failed to load job request.');
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    if (!confirm('Are you sure you want to delete this job request?')) return;

    try {
      await deleteJobRequest(Number(id), token!);
      navigate('/job-requests', { replace: true });
    } catch (err: any) {
      alert(err?.message || 'Failed to delete job request.');
    }
  }

  async function handleStatusChange(newStatus: JobStatus) {
    const confirmMsg =
      newStatus === 'cancelled'
        ? 'Are you sure you want to cancel this job request?'
        : `Change status to ${STATUS_LABELS[newStatus]}?`;

    if (!confirm(confirmMsg)) return;

    try {
      const res = await updateJobStatus(Number(id), newStatus, token!);
      setJobRequest(res.job_request);
    } catch (err: any) {
      alert(err?.message || 'Failed to update status.');
    }
  }

  const isEndUser = user?.role === 'end_user';
  const isCleaner = user?.role === 'cleaner';

  if (loading) {
    return (
      <>
        <Navbar />
        <main className="container py-5 text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </main>
      </>
    );
  }

  if (error || !jobRequest) {
    return (
      <>
        <Navbar />
        <main className="container py-5">
          <div className="alert alert-danger">{error || 'Job request not found.'}</div>
          <Link to="/job-requests" className="btn btn-primary">
            Back to Job Requests
          </Link>
        </main>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <main className="container py-5" style={{ maxWidth: 800 }}>
        <nav aria-label="breadcrumb" className="mb-3">
          <ol className="breadcrumb">
            <li className="breadcrumb-item">
              <Link to="/job-requests">Job Requests</Link>
            </li>
            <li className="breadcrumb-item active">#{jobRequest.id}</li>
          </ol>
        </nav>

        <div className="card shadow-sm">
          <div className="card-header d-flex justify-content-between align-items-center">
            <h1 className="h4 mb-0">{jobRequest.title}</h1>
            <span className={`badge bg-${STATUS_COLORS[jobRequest.status]} fs-6`}>
              {STATUS_LABELS[jobRequest.status]}
            </span>
          </div>

          <div className="card-body">
            {jobRequest.description && (
              <div className="mb-4">
                <h6 className="text-muted">Description</h6>
                <p className="mb-0">{jobRequest.description}</p>
              </div>
            )}

            <div className="row g-3 mb-4">
              <div className="col-md-6">
                <h6 className="text-muted">Service Type</h6>
                <p className="mb-0 text-capitalize">
                  {jobRequest.service_type || 'Not specified'}
                </p>
              </div>
              <div className="col-md-6">
                <h6 className="text-muted">Location</h6>
                <p className="mb-0">{jobRequest.location || 'Not specified'}</p>
              </div>
            </div>

            <div className="row g-3 mb-4">
              <div className="col-md-4">
                <h6 className="text-muted">Preferred Date</h6>
                <p className="mb-0">{jobRequest.preferred_date || 'Not specified'}</p>
              </div>
              <div className="col-md-4">
                <h6 className="text-muted">Start Time</h6>
                <p className="mb-0">{jobRequest.preferred_time_start || 'Not specified'}</p>
              </div>
              <div className="col-md-4">
                <h6 className="text-muted">End Time</h6>
                <p className="mb-0">{jobRequest.preferred_time_end || 'Not specified'}</p>
              </div>
            </div>

            <hr />

            <div className="row g-3 mb-4">
              <div className="col-md-6">
                <h6 className="text-muted">Requested By</h6>
                <p className="mb-0">{jobRequest.end_user?.email || 'Unknown'}</p>
              </div>
              <div className="col-md-6">
                <h6 className="text-muted">
                  {jobRequest.status === 'pending' ? 'Preferred Cleaner' : 'Assigned Cleaner'}
                </h6>
                <p className="mb-0">{jobRequest.cleaner?.email || 'Not assigned'}</p>
              </div>
            </div>

          </div>

          <div className="card-footer">
            <div className="d-flex gap-2 flex-wrap">
              <Link to="/job-requests" className="btn btn-secondary">
                Back to List
              </Link>

              {isEndUser && jobRequest.status === 'pending' && (
                <>
                  <Link
                    to={`/job-requests/${jobRequest.id}/edit`}
                    className="btn btn-primary"
                  >
                    Edit
                  </Link>
                  <button className="btn btn-danger" onClick={handleDelete}>
                    Delete
                  </button>
                </>
              )}

              {isEndUser && jobRequest.cleaner_id !== null && ['pending', 'confirmed'].includes(jobRequest.status) && (
                <button
                  className="btn btn-warning"
                  onClick={() => handleStatusChange('cancelled')}
                >
                  Cancel Request
                </button>
              )}

              {isCleaner && jobRequest.status === 'pending' && (
                <>
                  <button
                    className="btn btn-success"
                    onClick={() => handleStatusChange('confirmed')}
                  >
                    Accept Job
                  </button>
                  <button
                    className="btn btn-danger"
                    onClick={() => handleStatusChange('cancelled')}
                  >
                    Decline
                  </button>
                </>
              )}

              {isCleaner && jobRequest.status === 'confirmed' && (
                <>
                  <button
                    className="btn btn-primary"
                    onClick={() => handleStatusChange('in_progress')}
                  >
                    Start Job
                  </button>
                  <button
                    className="btn btn-danger"
                    onClick={() => handleStatusChange('cancelled')}
                  >
                    Cancel
                  </button>
                </>
              )}

              {isCleaner && jobRequest.status === 'in_progress' && (
                <button
                  className="btn btn-success"
                  onClick={() => handleStatusChange('completed')}
                >
                  Mark as Completed
                </button>
              )}
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
