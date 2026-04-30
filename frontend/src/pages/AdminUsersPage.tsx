import { useState, useEffect, useCallback } from 'react';
import Navbar from '../components/Navbar';
import {
  getAdminUsers,
  banUser,
  unbanUser,
  type AdminUser,
  type PaginationMeta,
} from '../api/admin';
import { getToken } from '../auth/storage';

const ROLE_LABELS: Record<string, string> = {
  end_user: 'End User',
  cleaner: 'Cleaner',
  administrator: 'Admin',
};

const ROLE_COLORS: Record<string, string> = {
  end_user: 'primary',
  cleaner: 'success',
  administrator: 'dark',
};

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export default function AdminUsersPage() {
  const USERS_PER_PAGE = 25;
  const token = getToken();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [roleFilter, setRoleFilter] = useState('');
  const [bannedFilter, setBannedFilter] = useState('');
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [page, setPage] = useState(1);
  const [banReason, setBanReason] = useState('');
  const [banningUserId, setBanningUserId] = useState<number | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('banned')) setBannedFilter(params.get('banned')!);
    if (params.get('role')) setRoleFilter(params.get('role')!);
    if (params.get('search')) {
      setSearch(params.get('search')!);
      setSearchInput(params.get('search')!);
    }
    const pageParam = Number(params.get('page'));
    if (Number.isInteger(pageParam) && pageParam > 0) setPage(pageParam);
  }, []);

  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params: { role?: string; banned?: string; search?: string; page?: number; perPage?: number } = {
        page,
        perPage: USERS_PER_PAGE,
      };
      if (roleFilter) params.role = roleFilter;
      if (bannedFilter) params.banned = bannedFilter;
      if (search) params.search = search;

      const res = await getAdminUsers(token!, params);
      setUsers(res.users);
      setPagination(res.pagination);
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to load users.'));
    } finally {
      setLoading(false);
    }
  }, [roleFilter, bannedFilter, search, token, page]);

  useEffect(() => {
    void fetchUsers();
  }, [fetchUsers]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (roleFilter) params.set('role', roleFilter);
    if (bannedFilter) params.set('banned', bannedFilter);
    if (search) params.set('search', search);
    if (page > 1) params.set('page', String(page));
    const query = params.toString();
    const newUrl = `${window.location.pathname}${query ? `?${query}` : ''}`;
    window.history.replaceState({}, '', newUrl);
  }, [roleFilter, bannedFilter, search, page]);

  async function handleBan(userId: number) {
    try {
      const res = await banUser(userId, token!, banReason || undefined);
      setUsers((prev) => prev.map((u) => (u.id === userId ? res.user : u)));
      setBanningUserId(null);
      setBanReason('');
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Failed to ban user.'));
    }
  }

  async function handleUnban(userId: number) {
    if (!confirm('Are you sure you want to unban this user?')) return;

    try {
      const res = await unbanUser(userId, token!);
      setUsers((prev) => prev.map((u) => (u.id === userId ? res.user : u)));
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Failed to unban user.'));
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
        <h1 className="h3 fw-bold mb-1">Manage Users</h1>
        <p className="text-muted mb-4">View and manage registered users on the platform.</p>

        <div className="d-flex align-items-center gap-3 mb-4 flex-wrap">
          <select
            className="form-select"
            style={{ maxWidth: 160 }}
            value={roleFilter}
            onChange={(e) => {
              setRoleFilter(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All Roles</option>
            <option value="end_user">End Users</option>
            <option value="cleaner">Cleaners</option>
            <option value="administrator">Administrators</option>
          </select>

          <select
            className="form-select"
            style={{ maxWidth: 140 }}
            value={bannedFilter}
            onChange={(e) => {
              setBannedFilter(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All Status</option>
            <option value="false">Active</option>
            <option value="true">Banned</option>
          </select>

          <form onSubmit={handleSearchSubmit} className="d-flex gap-2" style={{ maxWidth: 300 }}>
            <input
              type="text"
              className="form-control"
              placeholder="Search by email..."
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
        ) : users.length === 0 ? (
          <div className="alert alert-info">No users found.</div>
        ) : (
          <div className="card shadow-sm">
            <div className="table-responsive">
              <table className="table table-hover align-middle mb-0">
                <thead>
                  <tr>
                    <th className="text-muted small text-uppercase fw-semibold ps-3">User</th>
                    <th className="text-muted small text-uppercase fw-semibold">Email</th>
                    <th className="text-muted small text-uppercase fw-semibold">Role</th>
                    <th className="text-muted small text-uppercase fw-semibold">Status</th>
                    <th className="text-muted small text-uppercase fw-semibold">Last Login</th>
                    <th className="text-muted small text-uppercase fw-semibold">Joined</th>
                    <th className="text-muted small text-uppercase fw-semibold pe-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className={u.is_banned ? 'table-danger' : ''}>
                      <td className="ps-3 fw-medium">
                        {u.profile ? (
                          `${u.profile.first_name} ${u.profile.last_name}`
                        ) : (
                          <span className="text-muted fst-italic">No profile</span>
                        )}
                      </td>
                      <td>{u.email}</td>
                      <td>
                        <span className={`badge bg-${ROLE_COLORS[u.role] || 'secondary'}`}>
                          {ROLE_LABELS[u.role] || u.role}
                        </span>
                      </td>
                      <td>
                        {u.is_banned ? (
                          <>
                            <span className="badge bg-danger">Banned</span>
                            {u.ban_reason && (
                              <div className="text-muted small mt-1">{u.ban_reason}</div>
                            )}
                          </>
                        ) : (
                          <span className="badge bg-success">Active</span>
                        )}
                      </td>
                      <td className="text-muted small">
                        {u.last_login_at ? new Date(u.last_login_at).toLocaleDateString() : 'Never'}
                      </td>
                      <td className="text-muted small">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                      <td className="pe-3">
                        {u.role !== 'administrator' && (
                          <>
                            {u.is_banned ? (
                              <button
                                className="btn btn-sm btn-outline-success"
                                onClick={() => handleUnban(u.id)}
                              >
                                Unban
                              </button>
                            ) : banningUserId === u.id ? (
                              <div className="d-flex gap-1 align-items-center">
                                <input
                                  type="text"
                                  className="form-control form-control-sm"
                                  placeholder="Reason (optional)"
                                  value={banReason}
                                  onChange={(e) => setBanReason(e.target.value)}
                                  style={{ minWidth: 120 }}
                                />
                                <button
                                  className="btn btn-sm btn-danger"
                                  onClick={() => handleBan(u.id)}
                                >
                                  Confirm
                                </button>
                                <button
                                  className="btn btn-sm btn-secondary"
                                  onClick={() => {
                                    setBanningUserId(null);
                                    setBanReason('');
                                  }}
                                >
                                  Cancel
                                </button>
                              </div>
                            ) : (
                              <button
                                className="btn btn-sm btn-outline-danger"
                                onClick={() => setBanningUserId(u.id)}
                              >
                                Ban
                              </button>
                            )}
                          </>
                        )}
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
                  {pagination.total} users
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
