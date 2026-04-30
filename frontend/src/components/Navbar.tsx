import { Link, useNavigate } from 'react-router-dom';
import Logo from './Logo';
import { clearAuth, getUser } from '../auth/storage';

export default function Navbar() {
  const navigate = useNavigate();
  const user = getUser();

  function logout() {
    clearAuth();
    navigate('/', { replace: true });
  }

  return (
    <nav className="navbar bg-white border-bottom">
      <div className="container">
        <Link to={user ? '/dashboard' : '/login'} className="navbar-brand m-0">
          <Logo size="sm" />
        </Link>

        <div className="d-flex align-items-center gap-2">
          {!user ? (
            <>
              <Link to="/login" className="btn btn-outline-primary btn-sm">
                Login
              </Link>
              <Link to="/register" className="btn btn-primary btn-sm">
                Register
              </Link>
            </>
          ) : (
            <>
              <span className="text-muted small me-2">{user.email}</span>
              {user.role === 'cleaner' && (
                <Link to="/cleaner/profile" className="btn btn-outline-secondary btn-sm">
                  Cleaner Profile
                </Link>
              )}
              {user.role === 'end_user' && (
              <Link to="/cleaners" className="btn btn-outline-secondary btn-sm">
                  View Cleaners
                </Link>
              )}
              {user.role === 'administrator' && (
                <>
                  <Link to="/admin/users" className="btn btn-outline-secondary btn-sm">
                    Users
                  </Link>
                  <Link to="/admin/bookings" className="btn btn-outline-secondary btn-sm">
                    Bookings
                  </Link>
                </>
              )}
              <Link to="/profile" className="btn btn-outline-primary btn-sm">
                Profile
              </Link>
              <button onClick={logout} className="btn btn-outline-secondary btn-sm">
                Logout
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}