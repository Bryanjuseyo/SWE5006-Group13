import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import JobRequestFormFields from '../components/JobRequestFormFields';
import Navbar from '../components/Navbar';
import PreferredCleanerSelect from '../components/PreferredCleanerSelect';
import {
  getJobRequest,
  updateJobRequest,
  type ServiceType,
  type JobRequest,
} from '../api/job_requests';
import { getToken, getUser } from '../auth/storage';
import { useEligibleCleaners } from '../hooks/useEligibleCleaners';
import { getJobRequestFormError } from '../utils/jobRequestForm';

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
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const token = getToken();
  const user = getUser();
  const today = new Date().toISOString().split('T')[0];
  const now = new Date();
  const currentTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  const jobRequestId = Number(id);
  const {
    cleaners,
    preferredCleanerId,
    setPreferredCleanerId,
    canLoadCleaners,
  } = useEligibleCleaners({
    serviceType,
    preferredDate,
    preferredTimeStart,
    preferredTimeEnd,
    excludeJobRequestId: jobRequestId,
  });

  const fetchJobRequest = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getJobRequest(jobRequestId, token!);
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
  }, [jobRequestId, token, setPreferredCleanerId]);

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

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const validationError = getJobRequestFormError({
      title,
      serviceType,
      location,
      preferredDate,
      preferredTimeStart,
      preferredTimeEnd,
      today,
      currentTime,
      rejectPastDate: true,
    });
    if (validationError) {
      setError(validationError);
      return;
    }
    if (!serviceType) {
      setError('Service type is required.');
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
          <JobRequestFormFields
            title={title}
            description={description}
            serviceType={serviceType}
            location={location}
            preferredDate={preferredDate}
            preferredTimeStart={preferredTimeStart}
            preferredTimeEnd={preferredTimeEnd}
            today={today}
            currentTime={currentTime}
            onTitleChange={setTitle}
            onDescriptionChange={setDescription}
            onServiceTypeChange={setServiceType}
            onLocationChange={setLocation}
            onPreferredDateChange={setPreferredDate}
            onPreferredTimeStartChange={setPreferredTimeStart}
            onPreferredTimeEndChange={setPreferredTimeEnd}
          />

          <div className="mb-3">
            <label className="form-label">Preferred Cleaner (optional)</label>
            <PreferredCleanerSelect
              cleaners={cleaners}
              value={preferredCleanerId}
              canLoadCleaners={canLoadCleaners}
              emptyOptionLabel="No preference"
              helperText="You can change to a cleaner matching the selected service type, availability, and booking schedule."
              onChange={setPreferredCleanerId}
            />
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
