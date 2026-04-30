import { useState } from 'react';
import { Link, useLocation, useNavigate, type Location } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { login, verify2FA, resend2FA, type LoginSuccessResponse } from '../api/auth';
import { setAuth } from '../auth/storage';

type LoginLocationState = {
  fromRegister?: boolean;
};

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation() as Location<LoginLocationState>;

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [tempToken, setTempToken] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resendSuccess, setResendSuccess] = useState<string | null>(null);

  const fromRegister = location.state?.fromRegister;
  const requires2FA = tempToken !== null;

  async function onSubmitCredentials(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    try {
      setLoading(true);
      const res = await login({ email: email.trim().toLowerCase(), password });

      if ('requires_2fa' in res && res.requires_2fa) {
        setTempToken(res.temp_token);
      } else {
        const success = res as LoginSuccessResponse;
        setAuth(success.token, success.user);
        navigate('/dashboard', { replace: true });
      }
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Login failed.'));
    } finally {
      setLoading(false);
    }
  }

  async function onResendOtp() {
    setError(null);
    setResendSuccess(null);
    try {
      setLoading(true);
      const res = await resend2FA(tempToken!);
      setTempToken(res.temp_token);
      setResendSuccess('A new verification code has been sent to your email.');
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to resend code.'));
    } finally {
      setLoading(false);
    }
  }

  async function onSubmitOtp(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResendSuccess(null);

    try {
      setLoading(true);
      const res = await verify2FA(otp.trim(), tempToken!);
      setAuth(res.token, res.user);
      navigate('/dashboard', { replace: true });
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'OTP verification failed.'));
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

        {!requires2FA ? (
          <form onSubmit={onSubmitCredentials} className="card p-4 shadow-sm">
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
        ) : (
          <form onSubmit={onSubmitOtp} className="card p-4 shadow-sm">
            <div className="alert alert-info mb-3">
              A 6-digit verification code has been sent to <strong>{email}</strong>.
            </div>
            {resendSuccess && <div className="alert alert-success">{resendSuccess}</div>}

            <div className="mb-4">
              <label className="form-label">Verification Code</label>
              <input
                className="form-control form-control-lg text-center"
                type="text"
                inputMode="numeric"
                pattern="\d{6}"
                maxLength={6}
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                placeholder="000000"
                autoComplete="one-time-code"
                required
              />
              <div className="form-text">Enter the 6-digit code from your email.</div>
            </div>

            <button className="btn btn-primary w-100" disabled={loading}>
              {loading ? 'Verifying...' : 'Verify Code'}
            </button>

            <div className="d-flex justify-content-between mt-2">
              <button
                type="button"
                className="btn btn-link p-0"
                onClick={onResendOtp}
                disabled={loading}
              >
                Resend code
              </button>
              <button
                type="button"
                className="btn btn-link p-0"
                onClick={() => { setTempToken(null); setOtp(''); setError(null); setResendSuccess(null); }}
              >
                Back to login
              </button>
            </div>
          </form>
        )}
      </main>
    </>
  );
}
