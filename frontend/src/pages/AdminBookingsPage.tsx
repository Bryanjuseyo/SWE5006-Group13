import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { getAdminBookings, rejectBooking, type PaginationMeta } from '../api/admin';
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

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export default function AdminBookingsPage() {
  const BOOKINGS_PER_PAGE = 25;
  const token = getToken();
  const [bookings, setBookings] = useState<JobRequest[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [page, setPage] = useState(1);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const status = params.get('status');
    if (status) setStatusFilter(status);
    if (params.get('search')) {
      setSearch(params.get('search')!);
      setSearchInput(params.get('search')!);
    }
    const pageParam = Number(params.get('page'));
    if (Number.isInteger(pageParam) && pageParam > 0) setPage(pageParam);
  }, []);

  const fetchBookings = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params: { status?: string; search?: string; page?: number; perPage?: number } = {
        page,
        perPage: BOOKINGS_PER_PAGE,
      };
      if (statusFilter) params.status = statusFilter;
      if (search) params.search = search;

      const res = await getAdminBookings(token!, params);
      setBookings(res.job_requests);
      setPagination(res.pagination);
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to load bookings.'));
    } finally {
      setLoading(false);
    }
  }, [statusFilter, search, token, page]);

  useEffect(() => {
    void fetchBookings();
  }, [fetchBookings]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (statusFilter) params.set('status', statusFilter);
    if (search) params.set('search', search);
    if (page > 1) params.set('page', String(page));
    const query = params.toString();
    const newUrl = `${window.location.pathname}${query ? `?${query}` : ''}`;
    window.history.replaceState({}, '', newUrl);
  }, [statusFilter, search, page]);

  async function handleReject(id: number) {
    if (!confirm('Are you sure you want to reject this booking? This action marks it as suspicious.')) {
      return;
    }

    try {
      const res = await rejectBooking(id, token!);
      setBookings((prev) => prev.map((b) => (b.id === id ? res.job_request : b)));
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Failed to reject booking.'));
    }
  }

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSearch(searchInput.trim());
    setPage(1);
  }

  return (
    <>
      <Navbar />
      <main className="container py-5">
        <h1 className="h3 fw-bold mb-1">Manage Bookings</h1>
        <p className="text-muted mb-4">View and manage all jobs and bookings on the platform.</p>

        <div className="d-flex align-items-center gap-3 mb-4 flex-wrap">
          <select
            className="form-select"
            style={{ maxWidth: 180 }}
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
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
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
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
                      <td className="fw-medium">{b.title}</td>
                      <td className="text-muted">{b.end_user?.email || `User #${b.end_user_id}`}</td>
                      <td className="text-capitalize">{b.service_type || '-'}</td>
                      <td className="text-muted">
                        {b.cleaner?.email || <span className="fst-italic">Unassigned</span>}
                      </td>
                      <td>
                        <span className={`badge bg-${STATUS_COLORS[b.status] || 'secondary'}`}>
                          {STATUS_LABELS[b.status] || b.status}
                        </span>
                      </td>
                      <td className="text-muted small">{b.preferred_date || '-'}</td>
                      <td className="text-muted small">
                        {new Date(b.created_at).toLocaleDateString()}
                      </td>
                      <td className="pe-3">
                        <div className="d-flex gap-1">
                          <Link to={`/job-requests/${b.id}`} className="btn btn-sm btn-outline-dark">
                            View
                          </Link>
                          {b.status !== 'completed' &&
                            b.status !== 'rejected' &&
                            b.status !== 'cancelled' && (
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
            {pagination && (
              <div className="card-footer bg-white d-flex flex-column flex-md-row justify-content-between align-items-center gap-3">
                <div className="text-muted small">
                  Showing {(pagination.page - 1) * pagination.per_page + 1}-
                  {Math.min(pagination.page * pagination.per_page, pagination.total)} of{' '}
                  {pagination.total} bookings
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
          </div>
        )}
      </main>
    </>
  );
}
