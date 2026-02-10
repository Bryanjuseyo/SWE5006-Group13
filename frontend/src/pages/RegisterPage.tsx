import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { register, type UserRole } from '../api/auth';

function isValidEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function isValidPassword(pw: string) {
  if (pw.length < 8) return false;
  return /[A-Za-z]/.test(pw) && /\d/.test(pw);
}

export default function RegisterPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('end_user');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const eTrim = email.trim().toLowerCase();

    if (!isValidEmail(eTrim)) {
      setError('Please enter a valid email address.');
      return;
    }
    if (!isValidPassword(password)) {
      setError('Password must be at least 8 characters and contain letters and numbers.');
      return;
    }

    try {
      setLoading(true);
      await register({ email: eTrim, password, role });
      navigate('/login', { replace: true, state: { fromRegister: true } });
    } catch (err: any) {
      setError(err?.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="container py-5" style={{ maxWidth: 520 }}>
        <h1 className="h3 fw-bold mb-3">Create an account</h1>

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

          <div className="mb-3">
            <label className="form-label">Password</label>
            <input
              className="form-control"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 chars, letters + numbers"
              autoComplete="new-password"
              required
            />
          </div>

          <div className="mb-4">
            <label className="form-label">Role</label>
            <select
              className="form-select"
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole)}
            >
              <option value="end_user">End User</option>
              <option value="cleaner">Cleaner</option>
              <option value="administrator">Administrator</option>
            </select>
            <div className="form-text">
              (For demo/testing you can create an admin, but normally this would be restricted.)
            </div>
          </div>

          <button className="btn btn-primary w-100" disabled={loading}>
            {loading ? 'Creating account...' : 'Register'}
          </button>

          <div className="text-center mt-3">
            <span className="text-muted">Already have an account?</span>{' '}
            <Link to="/login">Login</Link>
          </div>
        </form>
      </main>
    </>
  );
}
