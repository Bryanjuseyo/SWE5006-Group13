import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { getAdminBookings, rejectBooking } from '../api/admin';
import { getToken } from '../auth/storage';
import type { JobRequest } from '../api/job_requests';

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  confirmed: 'Confirmed',
  in_progress: 'In Progress',
  completed: 'Completed',
  cancelled: 'Cancelled',
  rejected: 'Rejected',
};

const STATUS_COLORS: Record<string, string> = {
  pending: 'warning',
  confirmed: 'info',
  in_progress: 'primary',
  completed: 'success',
  cancelled: 'secondary',
  rejected: 'danger',
};

export default function AdminBookingsPage() {
  const token = getToken();
  const [bookings, setBookings] = useState<JobRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('status')) setStatusFilter(params.get('status')!);
  }, []);

  useEffect(() => {
    fetchBookings();
  }, [statusFilter]);

  async function fetchBookings() {
    try {
      setLoading(true);
      setError(null);
      const params: { status?: string; search?: string } = {};
      if (statusFilter) params.status = statusFilter;
      if (search) params.search = search;
      const res = await getAdminBookings(token!, params);
      setBookings(res.job_requests);
    } catch (err: any) {
      setError(err?.message || 'Failed to load bookings.');
    } finally {
      setLoading(false);
    }
  }

  async function handleReject(id: number) {
    if (!confirm('Are you sure you want to reject this booking? This action marks it as suspicious.')) return;
    try {
      const res = await rejectBooking(id, token!);
      setBookings((prev) => prev.map((b) => (b.id === id ? res.job_request : b)));
    } catch (err: any) {
      alert(err?.message || 'Failed to reject booking.');
    }
  }

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    fetchBookings();
  }

  return (
    <>
      <Navbar />
      <main className="container py-5">
        <h1 className="h3 fw-bold mb-1">Manage Bookings</h1>
        <p className="text-muted mb-4">View and manage all jobs and bookings on the platform.</p>

        {/* Filters */}
        <div className="d-flex align-items-center gap-3 mb-4 flex-wrap">
          <select
            className="form-select"
            style={{ maxWidth: 180 }}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="confirmed">Confirmed</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
            <option value="rejected">Rejected</option>
          </select>
          <form onSubmit={handleSearchSubmit} className="d-flex gap-2" style={{ maxWidth: 300 }}>
            <input
              type="text"
              className="form-control"
              placeholder="Search by title..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <button type="submit" className="btn btn-outline-primary btn-sm">
              Search
            </button>
          </form>
        </div>

        {error && <div className="alert alert-danger">{error}</div>}

        {loading ? (
          <div className="text-center py-5">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
          </div>
        ) : bookings.length === 0 ? (
          <div className="alert alert-info">
            {statusFilter
              ? `No bookings with status "${STATUS_LABELS[statusFilter]}" found.`
              : 'No bookings found.'}
          </div>
        ) : (
          <div className="card shadow-sm">
            <div className="table-responsive">
              <table className="table table-hover align-middle mb-0">
                <thead>
                  <tr>
                    <th className="text-muted small text-uppercase fw-semibold ps-3">ID</th>
                    <th className="text-muted small text-uppercase fw-semibold">Booking</th>
                    <th className="text-muted small text-uppercase fw-semibold">Client</th>
                    <th className="text-muted small text-uppercase fw-semibold">Service</th>
                    <th className="text-muted small text-uppercase fw-semibold">Cleaner</th>
                    <th className="text-muted small text-uppercase fw-semibold">Status</th>
                    <th className="text-muted small text-uppercase fw-semibold">Date</th>
                    <th className="text-muted small text-uppercase fw-semibold">Created</th>
                    <th className="text-muted small text-uppercase fw-semibold pe-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {bookings.map((b) => (
                    <tr key={b.id} className={b.status === 'rejected' ? 'table-danger' : ''}>
                      <td className="ps-3 text-muted">#{b.id}</td>
                      <td className="fw-medium">
                        {b.title}
                      </td>
                      <td className="text-muted">{b.end_user?.email || `User #${b.end_user_id}`}</td>
                      <td className="text-capitalize">{b.service_type || '-'}</td>
                      <td className="text-muted">{b.cleaner?.email || <span className="fst-italic">Unassigned</span>}</td>
                      <td>
                        <span className={`badge bg-${STATUS_COLORS[b.status] || 'secondary'}`}>
                          {STATUS_LABELS[b.status] || b.status}
                        </span>
                      </td>
                      <td className="text-muted small">{b.preferred_date || '-'}</td>
                      <td className="text-muted small">{new Date(b.created_at).toLocaleDateString()}</td>
                      <td className="pe-3">
                        <div className="d-flex gap-1">
                          <Link to={`/job-requests/${b.id}`} className="btn btn-sm btn-outline-dark">
                            View
                          </Link>
                          {b.status !== 'completed' && b.status !== 'rejected' && b.status !== 'cancelled' && (
                            <button
                              className="btn btn-sm btn-outline-danger"
                              onClick={() => handleReject(b.id)}
                            >
                              Reject
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
