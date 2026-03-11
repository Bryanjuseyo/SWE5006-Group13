import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { getToken, getUser } from '../auth/storage';
import { getAvailableJobs, updateJobStatus, type JobRequest } from '../api/job_requests';

function formatDate(d: string) {
  return new Date(d + 'T00:00:00').toLocaleDateString(undefined, {
    weekday: 'short', year: 'numeric', month: 'short', day: 'numeric',
  });
}

function formatTime(t: string | null) {
  if (!t) return null;
  const [h, m] = t.split(':');
  const date = new Date();
  date.setHours(Number(h), Number(m));
  return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

export default function BrowseJobsPage() {
  const token = getToken();
  const currentUser = getUser();
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<JobRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [accepting, setAccepting] = useState<number | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await getAvailableJobs(token!);
      setJobs(res.job_requests);
    } catch (e: any) {
      setError(e?.message || 'Failed to load available jobs.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleAccept(id: number) {
    setAccepting(id);
    try {
      await updateJobStatus(id, 'confirmed', token!);
      // Remove accepted job from the list and navigate to schedule
      setJobs((prev) => prev.filter((j) => j.id !== id));
      navigate('/cleaner/schedule');
    } catch (e: any) {
      alert(e?.message || 'Failed to accept job.');
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
        )}
      </main>
    </>
  );
}
