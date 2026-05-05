import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import JobRequestFormFields from '../components/JobRequestFormFields';
import Navbar from '../components/Navbar';
import PreferredCleanerSelect from '../components/PreferredCleanerSelect';
import {
  createJobRequest,
  type ServiceType,
} from '../api/job_requests';
import { getToken, getUser } from '../auth/storage';
import { autoAssignCleaner } from '../api/admin';
import { useEligibleCleaners } from '../hooks/useEligibleCleaners';
import { getJobRequestFormError } from '../utils/jobRequestForm';

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export default function CreateJobRequestPage() {
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [serviceType, setServiceType] = useState<ServiceType | ''>('');
  const [location, setLocation] = useState('');
  const [preferredDate, setPreferredDate] = useState('');
  const [preferredTimeStart, setPreferredTimeStart] = useState('');
  const [preferredTimeEnd, setPreferredTimeEnd] = useState('');
  const [cleanerMode, setCleanerMode] = useState<'auto' | 'manual'>('auto');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const token = getToken();
  const user = getUser();

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }
    if (user?.role !== 'end_user') {
      navigate('/job-requests');
    }
  }, [token, user, navigate]);

  const today = new Date().toISOString().split('T')[0];
  const now = new Date();
  const currentTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
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
  });

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
      setLoading(true);
      const res = await createJobRequest(
        {
          title: title.trim(),
          description: description.trim() || undefined,
          service_type: serviceType,
          location: location.trim(),
          preferred_date: preferredDate,
          preferred_time_start: preferredTimeStart || undefined,
          preferred_time_end: preferredTimeEnd || undefined,
          cleaner_id:
            cleanerMode === 'manual' && preferredCleanerId !== ''
              ? preferredCleanerId
              : null,
        },
        token!
      );

      if (cleanerMode === 'auto') {
        try {
          await autoAssignCleaner(res.job_request.id, token!);
        } catch {
          // Auto-match is best-effort; job is still created
        }
      }

      navigate('/job-requests', { replace: true });
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to create job request.'));
    } finally {
      setLoading(false);
    }
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
            <li className="breadcrumb-item active">New</li>
          </ol>
        </nav>

        <h1 className="h3 fw-bold mb-3">Create Job Request</h1>

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
            <label className="form-label fw-semibold">Cleaner Selection</label>
            <div className="d-flex rounded overflow-hidden border mb-3" style={{ maxWidth: 360 }}>
              <button
                type="button"
                className={`btn flex-fill rounded-0 border-0 ${cleanerMode === 'auto' ? 'btn-primary' : 'btn-light'
                  }`}
                onClick={() => {
                  setCleanerMode('auto');
                  setPreferredCleanerId('');
                }}
              >
                Auto-match
              </button>
              <button
                type="button"
                className={`btn flex-fill rounded-0 border-0 ${cleanerMode === 'manual' ? 'btn-primary' : 'btn-light'
                  }`}
                onClick={() => setCleanerMode('manual')}
              >
                Choose a cleaner
              </button>
            </div>

            {cleanerMode === 'auto' ? (
              <div className="form-text">
                We&apos;ll automatically match the best available cleaner based on your
                service type, date, and location.
              </div>
            ) : (
              <PreferredCleanerSelect
                cleaners={cleaners}
                value={preferredCleanerId}
                canLoadCleaners={canLoadCleaners}
                emptyOptionLabel="Select a cleaner..."
                helperText="Only showing cleaners that match the service type, availability, and booking schedule."
                onChange={setPreferredCleanerId}
              />
            )}
          </div>

          <div className="d-flex gap-2">
            <button className="btn btn-primary" disabled={loading}>
              {loading ? 'Creating...' : 'Create job request'}
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
