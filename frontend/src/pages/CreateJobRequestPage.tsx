import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import {
  createJobRequest,
  type ServiceType,
} from '../api/job_requests';

export default function CreateJobRequestPage() {
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [serviceType, setServiceType] = useState<ServiceType | ''>('');
  const [location, setLocation] = useState('');
  const [preferredDate, setPreferredDate] = useState('');
  const [preferredTimeStart, setPreferredTimeStart] = useState('');
  const [preferredTimeEnd, setPreferredTimeEnd] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const token = localStorage.getItem('cm_token');
  const user = JSON.parse(localStorage.getItem('cm_user') || '{}');

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }
    if (user?.role !== 'end_user') {
      navigate('/job-requests');
      return;
    }
  }, [token, user]);

  const today = new Date().toISOString().split('T')[0];
  const now = new Date();
  const currentTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

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

    if (preferredTimeStart && preferredDate === today && preferredTimeStart < currentTime) {
      setError('Start time cannot be in the past.');
      return;
    }

    if (preferredTimeStart && preferredTimeEnd && preferredTimeEnd <= preferredTimeStart) {
      setError('End time must be strictly after start time.');
      return;
    }

    try {
      setLoading(true);
      await createJobRequest(
        {
          title: title.trim(),
          description: description.trim() || undefined,
          service_type: serviceType,
          location: location.trim(),
          preferred_date: preferredDate,
          preferred_time_start: preferredTimeStart || undefined,
          preferred_time_end: preferredTimeEnd || undefined,
        },
        token!
      );
      navigate('/job-requests', { replace: true });
    } catch (err: any) {
      setError(err?.message || 'Failed to create job request.');
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
                min={new Date().toISOString().split('T')[0]}
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

          <div className="d-flex gap-2">
            <button className="btn btn-primary" disabled={loading}>
              {loading ? 'Creating...' : 'Create Job Request'}
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
