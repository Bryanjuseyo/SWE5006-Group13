import { Link, useNavigate } from 'react-router-dom';
import Logo from './Logo';

export default function Navbar() {
  const navigate = useNavigate();
  const token = localStorage.getItem('cm_token');
  const user = JSON.parse(localStorage.getItem('cm_user') || 'null');

  function handleLogout() {
    localStorage.removeItem('cm_token');
    localStorage.removeItem('cm_user');
    navigate('/login');
  }

  return (
    <nav className="navbar bg-white border-bottom">
      <div className="container">
        <Link to="/" className="navbar-brand m-0">
          <Logo size="sm" />
        </Link>

        <div className="d-flex align-items-center gap-3">
          {token && user ? (
            <>
              {(user.role === 'end_user' || user.role === 'cleaner') && (
                <Link to="/job-requests" className="nav-link">
                  Job Requests
                </Link>
              )}
              <span className="text-muted small">{user.email}</span>
              <button
                className="btn btn-outline-secondary btn-sm"
                onClick={handleLogout}
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-outline-primary btn-sm">
                Login
              </Link>
              <Link to="/register" className="btn btn-primary btn-sm">
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
