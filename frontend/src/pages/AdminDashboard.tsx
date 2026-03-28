import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { getAdminStats, getAdminBookings, rejectBooking, type DashboardStats } from '../api/admin';
import { getToken } from '../auth/storage';
import type { JobRequest } from '../api/job_requests';

const NAV_CARDS = [
  {
    to: '/admin/users',
    title: 'Manage Users',
    description: 'View and manage all registered users. Ban or unban malicious accounts.',
    btnLabel: 'View Users',
    btnClass: 'btn-primary',
  },
  {
    to: '/admin/bookings',
    title: 'Manage Bookings',
    description: 'View all job requests and bookings. Reject suspicious or fraudulent entries.',
    btnLabel: 'View Bookings',
    btnClass: 'btn-outline-dark',
  },
];

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

const STATUS_DOT_COLORS: Record<string, string> = {
  pending: '#e67e22',
  confirmed: '#2980b9',
  in_progress: '#16a085',
  completed: '#27ae60',
  cancelled: '#95a5a6',
  rejected: '#e74c3c',
};

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export default function AdminDashboard() {
  const token = getToken();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentBookings, setRecentBookings] = useState<JobRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        const [statsData, bookingsData] = await Promise.all([
          getAdminStats(token!),
          getAdminBookings(token!),
        ]);

        setStats(statsData);
        setRecentBookings(bookingsData.job_requests.slice(0, 5));
      } catch (err: unknown) {
        setError(getErrorMessage(err, 'Failed to load dashboard.'));
      } finally {
        setLoading(false);
      }
    }

    void fetchData();
  }, [token]);

  async function handleReject(id: number) {
    if (!confirm('Are you sure you want to reject this booking?')) return;

    try {
      const res = await rejectBooking(id, token!);
      setRecentBookings((prev) => prev.map((b) => (b.id === id ? res.job_request : b)));
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Failed to reject booking.'));
    }
  }

  return (
    <>
      <Navbar />
      <main className="container py-5">
        <h1 className="h3 fw-bold mb-1">Admin Dashboard</h1>
        <p className="text-muted mb-4">Monitor and manage platform activities.</p>

        {error && <div className="alert alert-danger">{error}</div>}

        {loading ? (
          <div className="text-center py-5">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
          </div>
        ) : (
          <>
            <div className="row g-4 mb-5">
              {NAV_CARDS.map((card) => (
                <div key={card.to} className="col-12 col-md-4">
                  <div className="card h-100 shadow-sm">
                    <div className="card-body d-flex flex-column">
                      <h5 className="card-title fw-semibold">{card.title}</h5>
                      <p className="card-text text-muted flex-grow-1">{card.description}</p>
                      <Link to={card.to} className={`btn ${card.btnClass} mt-2 align-self-start`}>
                        {card.btnLabel}
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {stats && (
              <>
                <h2 className="h5 fw-bold mb-3">Users</h2>
                <div className="row g-3 mb-5">
                  {[
                    { label: 'Total Users', value: stats.users.total, borderColor: '#2563eb' },
                    { label: 'End Users', value: stats.users.end_users, borderColor: '#3b82f6' },
                    { label: 'Cleaners', value: stats.users.cleaners, borderColor: '#16a34a' },
                    { label: 'Admins', value: stats.users.administrators, borderColor: '#dc2626' },
                  ].map((item) => (
                    <div key={item.label} className="col-6 col-lg-3">
                      <div
                        className="card h-100"
                        style={{
                          borderLeft: `4px solid ${item.borderColor}`,
                          borderTop: 'none',
                          borderRight: '1px solid #e5e7eb',
                          borderBottom: '1px solid #e5e7eb',
                        }}
                      >
                        <div className="card-body">
                          <div className="text-muted small text-uppercase fw-semibold">
                            {item.label}
                          </div>
                          <div className="h2 fw-bold mb-0 mt-1">{item.value}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <h2 className="h5 fw-bold mb-3">Jobs & Bookings</h2>
                <div className="card shadow-sm mb-5">
                  <div className="card-body">
                    <div className="d-flex justify-content-between align-items-center mb-3">
                      <span className="fw-semibold">Booking status breakdown</span>
                      <span>
                        <strong>{stats.jobs.total}</strong>{' '}
                        <span className="text-muted">total jobs</span>
                      </span>
                    </div>

                    {stats.jobs.total > 0 ? (
                      <div className="d-flex rounded overflow-hidden mb-3" style={{ height: 10 }}>
                        {[
                          { key: 'pending', value: stats.jobs.pending },
                          { key: 'confirmed', value: stats.jobs.confirmed },
                          { key: 'in_progress', value: stats.jobs.in_progress },
                          { key: 'completed', value: stats.jobs.completed },
                          { key: 'cancelled', value: stats.jobs.cancelled },
                          { key: 'rejected', value: stats.jobs.rejected },
                        ]
                          .filter((s) => s.value > 0)
                          .map((s) => (
                            <div
                              key={s.key}
                              style={{
                                width: `${(s.value / stats.jobs.total) * 100}%`,
                                backgroundColor: STATUS_DOT_COLORS[s.key],
                              }}
                            />
                          ))}
                      </div>
                    ) : (
                      <div className="bg-light rounded mb-3" style={{ height: 10 }} />
                    )}

                    <div className="d-flex flex-wrap gap-3">
                      {[
                        { key: 'pending', value: stats.jobs.pending },
                        { key: 'confirmed', value: stats.jobs.confirmed },
                        { key: 'in_progress', value: stats.jobs.in_progress },
                        { key: 'completed', value: stats.jobs.completed },
                        { key: 'cancelled', value: stats.jobs.cancelled },
                        { key: 'rejected', value: stats.jobs.rejected },
                      ].map((s) => (
                        <Link
                          key={s.key}
                          to={`/admin/bookings?status=${s.key}`}
                          className="text-decoration-none d-flex align-items-center gap-1"
                        >
                          <span
                            className="rounded-circle d-inline-block"
                            style={{
                              width: 10,
                              height: 10,
                              backgroundColor: STATUS_DOT_COLORS[s.key],
                            }}
                          />
                          <span className="text-dark small">{STATUS_LABELS[s.key]}</span>
                          <strong className="small">{s.value}</strong>
                        </Link>
                      ))}
                    </div>
                  </div>
                </div>

                <h2 className="h5 fw-bold mb-3">Recent Bookings</h2>
                <div className="card shadow-sm">
                  {recentBookings.length === 0 ? (
                    <div className="card-body text-center text-muted py-4">No bookings yet.</div>
                  ) : (
                    <div className="table-responsive">
                      <table className="table table-hover align-middle mb-0">
                        <thead>
                          <tr>
                            <th className="text-muted small text-uppercase fw-semibold ps-3">ID</th>
                            <th className="text-muted small text-uppercase fw-semibold">Booking</th>
                            <th className="text-muted small text-uppercase fw-semibold">User</th>
                            <th className="text-muted small text-uppercase fw-semibold">Service</th>
                            <th className="text-muted small text-uppercase fw-semibold">Status</th>
                            <th className="text-muted small text-uppercase fw-semibold">Date</th>
                            <th className="text-muted small text-uppercase fw-semibold pe-3">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {recentBookings.map((b) => (
                            <tr key={b.id}>
                              <td className="ps-3 text-muted">#{b.id}</td>
                              <td className="fw-medium">{b.title}</td>
                              <td className="text-muted">{b.end_user?.email || '-'}</td>
                              <td className="text-capitalize">{b.service_type}</td>
                              <td>
                                <span className={`badge bg-${STATUS_COLORS[b.status] || 'secondary'}`}>
                                  {STATUS_LABELS[b.status] || b.status}
                                </span>
                              </td>
                              <td>{b.preferred_date || '-'}</td>
                              <td className="pe-3">
                                <div className="d-flex gap-1">
                                  <Link
                                    to={`/job-requests/${b.id}`}
                                    className="btn btn-sm btn-outline-dark"
                                  >
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
                  )}
                  <div className="card-footer bg-white text-center">
                    <Link to="/admin/bookings" className="text-decoration-none small">
                      View all bookings
                    </Link>
                  </div>
                </div>
              </>
            )}
          </>
        )}
      </main>
    </>
  );
}