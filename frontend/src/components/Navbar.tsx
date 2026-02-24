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
        <Link to="/" className="navbar-brand m-0">
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