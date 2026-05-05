import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import {
  getJobRequest,
  updateJobRequest,
  type ServiceType,
  type JobRequest,
} from '../api/job_requests';
import { getToken, getUser } from '../auth/storage';

import { listCleaners } from '../api/cleaners';
import type { CleanerListItem } from '../api/cleaners';

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export default function EditJobRequestPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const [jobRequest, setJobRequest] = useState<JobRequest | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [serviceType, setServiceType] = useState<ServiceType | ''>('');
  const [location, setLocation] = useState('');
  const [preferredDate, setPreferredDate] = useState('');
  const [preferredTimeStart, setPreferredTimeStart] = useState('');
  const [preferredTimeEnd, setPreferredTimeEnd] = useState('');
  const [cleaners, setCleaners] = useState<CleanerListItem[]>([]);
  const [preferredCleanerId, setPreferredCleanerId] = useState<number | ''>('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const token = getToken();
  const user = getUser();

  const fetchJobRequest = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getJobRequest(Number(id), token!);
      const job = res.job_request;
      setJobRequest(job);

      setTitle(job.title);
      setDescription(job.description || '');
      setServiceType(job.service_type || '');
      setLocation(job.location || '');
      setPreferredDate(job.preferred_date || '');
      setPreferredTimeStart(job.preferred_time_start ? job.preferred_time_start.slice(0, 5) : '');
      setPreferredTimeEnd(job.preferred_time_end ? job.preferred_time_end.slice(0, 5) : '');
      setPreferredCleanerId(job.cleaner_id ?? '');
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to load job request.'));
    } finally {
      setLoading(false);
    }
  }, [id, token]);

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }
    if (user?.role !== 'end_user') {
      navigate('/job-requests');
      return;
    }
    void fetchJobRequest();
  }, [token, user?.role, navigate, fetchJobRequest]);

  const today = new Date().toISOString().split('T')[0];
  const now = new Date();
  const currentTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  const canLoadCleaners = Boolean(serviceType && preferredDate);

  useEffect(() => {
    let mounted = true;

    if (!canLoadCleaners) {
      setCleaners([]);
      setPreferredCleanerId('');
      return () => {
        mounted = false;
      };
    }

    (async () => {
      try {
        const res = await listCleaners({
          service_type: serviceType as ServiceType,
          preferred_date: preferredDate,
          preferred_time_start: preferredTimeStart || undefined,
          preferred_time_end: preferredTimeEnd || undefined,
          exclude_job_request_id: Number(id),
        });
        if (!mounted) return;

        setCleaners(res.cleaners);
        setPreferredCleanerId((current) => (
          current !== '' && !res.cleaners.some((c) => c.user_id === current) ? '' : current
        ));
      } catch (e: unknown) {
        console.error(e);
        if (mounted) {
          setCleaners([]);
          setPreferredCleanerId('');
        }
      }
    })();

    return () => {
      mounted = false;
    };
  }, [canLoadCleaners, id, serviceType, preferredDate, preferredTimeStart, preferredTimeEnd]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!title.trim()) {
      setError('Title is required.');
      return;
    }
    if (!serviceType) {
      setError('Service type is required.');
      return;
    }
    if (!location.trim()) {
      setError('Location is required.');
      return;
    }
    if (!preferredDate) {
      setError('Preferred date is required.');
      return;
    }
    if (preferredDate < today) {
      setError('Preferred date cannot be in the past.');
      return;
    }

    if (preferredTimeStart && preferredDate === today && preferredTimeStart < currentTime) {
      setError('Start time cannot be in the past.');
      return;
    }

    if (preferredTimeStart && preferredTimeEnd && preferredTimeEnd <= preferredTimeStart) {
      setError('End time must be strictly after start time.');
      return;
    }

    try {
      setSaving(true);
      await updateJobRequest(
        Number(id),
        {
          title: title.trim(),
          description: description.trim() || undefined,
          service_type: serviceType,
          location: location.trim(),
          preferred_date: preferredDate,
          preferred_time_start: preferredTimeStart || null,
          preferred_time_end: preferredTimeEnd || null,
          cleaner_id: preferredCleanerId === '' ? null : preferredCleanerId,
        },
        token!
      );
      navigate('/job-requests', { replace: true });
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to update job request.'));
    } finally {
      setSaving(false);
    }
  }

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

  if (!jobRequest) {
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

  if (jobRequest.status !== 'pending') {
    return (
      <>
        <Navbar />
        <main className="container py-5">
          <div className="alert alert-warning">Only pending job requests can be edited.</div>
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
      <main className="container py-5" style={{ maxWidth: 720 }}>
        <nav aria-label="breadcrumb" className="mb-3">
          <ol className="breadcrumb">
            <li className="breadcrumb-item">
              <Link to="/job-requests">Job Requests</Link>
            </li>
            <li className="breadcrumb-item">
              <Link to={`/job-requests/${id}`}>#{id}</Link>
            </li>
            <li className="breadcrumb-item active">Edit</li>
          </ol>
        </nav>

        <h1 className="h3 fw-bold mb-3">Edit Job Request</h1>

        {error && <div className="alert alert-danger">{error}</div>}

        <form onSubmit={onSubmit} className="card p-4 shadow-sm">
          <div className="mb-3">
            <label className="form-label">
              Title <span className="text-danger">*</span>
            </label>
            <input
              className="form-control"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Weekly house cleaning"
              required
            />
          </div>

          <div className="mb-3">
            <label className="form-label">Description</label>
            <textarea
              className="form-control"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your cleaning requirements..."
            />
          </div>

          <div className="row mb-3">
            <div className="col-md-6">
              <label className="form-label">
                Service Type <span className="text-danger">*</span>
              </label>
              <select
                className="form-select"
                value={serviceType}
                onChange={(e) => setServiceType(e.target.value as ServiceType | '')}
                required
              >
                <option value="">Select type...</option>
                <option value="partial">Partial Cleaning</option>
                <option value="full">Full Cleaning</option>
              </select>
            </div>
            <div className="col-md-6">
              <label className="form-label">
                Location <span className="text-danger">*</span>
              </label>
              <input
                className="form-control"
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g., 123 Main St, Singapore"
                required
              />
            </div>
          </div>

          <div className="row mb-3">
            <div className="col-md-4">
              <label className="form-label">
                Preferred Date <span className="text-danger">*</span>
              </label>
              <input
                className="form-control"
                type="date"
                value={preferredDate}
                onChange={(e) => setPreferredDate(e.target.value)}
                min={today}
                required
              />
            </div>
            <div className="col-md-4">
              <label className="form-label">Start Time</label>
              <input
                className="form-control"
                type="time"
                value={preferredTimeStart}
                onChange={(e) => setPreferredTimeStart(e.target.value)}
                min={preferredDate === today ? currentTime : undefined}
              />
            </div>
            <div className="col-md-4">
              <label className="form-label">End Time</label>
              <input
                className="form-control"
                type="time"
                value={preferredTimeEnd}
                onChange={(e) => setPreferredTimeEnd(e.target.value)}
                min={preferredTimeStart || undefined}
              />
            </div>
          </div>

          <div className="mb-3">
            <label className="form-label">Preferred Cleaner (optional)</label>
            <select
              className="form-select"
              value={preferredCleanerId}
              disabled={!canLoadCleaners}
              onChange={(e) => {
                const v = e.target.value;
                setPreferredCleanerId(v === '' ? '' : Number(v));
              }}
            >
              <option value="">
                {!canLoadCleaners
                  ? 'Select service type and date first'
                  : cleaners.length === 0
                    ? 'No eligible cleaners available'
                    : 'No preference'}
              </option>
              {cleaners.map((c) => (
                <option key={c.user_id} value={c.user_id}>
                  {c.first_name} {c.last_name} - {c.cleaner_profile.service_type} -{' '}
                  {c.cleaner_profile.hourly_rate != null
                    ? `$${c.cleaner_profile.hourly_rate}/hr`
                    : 'Rate N/A'}{' '}
                  - {c.cleaner_profile.years_experience} yrs
                </option>
              ))}
            </select>
            <div className="form-text">
              You can change to a cleaner matching the selected service type, availability, and booking schedule.
            </div>
          </div>

          <div className="d-flex gap-2">
            <button className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
            <Link to="/job-requests" className="btn btn-outline-secondary">
              Cancel
            </Link>
          </div>
        </form>
      </main>
    </>
  );
}
