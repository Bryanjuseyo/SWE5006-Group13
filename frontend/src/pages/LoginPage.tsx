import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { login } from '../api/auth';

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation() as any;

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fromRegister = location?.state?.fromRegister;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    try {
      setLoading(true);
      const res = await login({ email: email.trim().toLowerCase(), password });

      // store token (recommended option A)
      localStorage.setItem('cm_token', res.token);
      localStorage.setItem('cm_user', JSON.stringify(res.user));

      // for now go home; later we’ll route to /dashboard
      navigate('/', { replace: true });
    } catch (err: any) {
      setError(err?.message || 'Login failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="container py-5" style={{ maxWidth: 520 }}>
        <h1 className="h3 fw-bold mb-3">Login</h1>

        {fromRegister && (
          <div className="alert alert-success">
            Registration successful. Please login.
          </div>
        )}

        {error && <div className="alert alert-danger">{error}</div>}

        <form onSubmit={onSubmit} className="card p-4 shadow-sm">
          <div className="mb-3">
            <label className="form-label">Email</label>
            <input
              className="form-control"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              required
            />
          </div>

          <div className="mb-4">
            <label className="form-label">Password</label>
            <input
              className="form-control"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>

          <button className="btn btn-primary w-100" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>

          <div className="text-center mt-3">
            <span className="text-muted">No account?</span>{' '}
            <Link to="/register">Register</Link>
          </div>
        </form>
      </main>
    </>
  );
}
