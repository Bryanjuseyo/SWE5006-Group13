import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { get2FAStatus, setup2FA, enable2FA, disable2FA } from '../api/auth';
import { getToken } from '../auth/storage';

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

export default function TwoFactorSetupPage() {
  const token = getToken()!;

  const [enabled, setEnabled] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [statusError, setStatusError] = useState<string | null>(null);

  // Enable flow
  const [sendingOtp, setSendingOtp] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [otp, setOtp] = useState('');
  const [enabling, setEnabling] = useState(false);
  const [enableError, setEnableError] = useState<string | null>(null);
  const [enableSuccess, setEnableSuccess] = useState<string | null>(null);

  // Disable flow
  const [password, setPassword] = useState('');
  const [disabling, setDisabling] = useState(false);
  const [disableError, setDisableError] = useState<string | null>(null);
  const [disableSuccess, setDisableSuccess] = useState<string | null>(null);

  useEffect(() => {
    async function loadStatus() {
      try {
        const res = await get2FAStatus(token);
        setEnabled(res.two_factor_enabled);
      } catch (e) {
        setStatusError(getErrorMessage(e, 'Failed to load 2FA status.'));
      } finally {
        setLoadingStatus(false);
      }
    }
    void loadStatus();
  }, [token]);

  async function handleSendOtp() {
    setSendingOtp(true);
    setEnableError(null);
    try {
      await setup2FA(token);
      setOtpSent(true);
    } catch (e) {
      setEnableError(getErrorMessage(e, 'Failed to send OTP.'));
    } finally {
      setSendingOtp(false);
    }
  }

  async function handleEnable(e: React.FormEvent) {
    e.preventDefault();
    setEnabling(true);
    setEnableError(null);
    try {
      await enable2FA(otp.trim(), token);
      setEnabled(true);
      setOtpSent(false);
      setOtp('');
      setEnableSuccess('Two-factor authentication has been enabled.');
    } catch (err) {
      setEnableError(getErrorMessage(err, 'Failed to enable 2FA.'));
    } finally {
      setEnabling(false);
    }
  }

  async function handleDisable(e: React.FormEvent) {
    e.preventDefault();
    setDisabling(true);
    setDisableError(null);
    try {
      await disable2FA(password, token);
      setEnabled(false);
      setPassword('');
      setDisableSuccess('Two-factor authentication has been disabled.');
    } catch (err) {
      setDisableError(getErrorMessage(err, 'Failed to disable 2FA.'));
    } finally {
      setDisabling(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="container py-5" style={{ maxWidth: 600 }}>
        <nav aria-label="breadcrumb" className="mb-3">
          <ol className="breadcrumb">
            <li className="breadcrumb-item"><Link to="/profile">Profile</Link></li>
            <li className="breadcrumb-item active">Two-Factor Authentication</li>
          </ol>
        </nav>

        <h1 className="h3 fw-bold mb-1">Two-Factor Authentication</h1>
        <p className="text-muted mb-4">
          Secure your account by requiring a verification code from your email each time you log in.
        </p>

        {loadingStatus ? (
          <div className="text-muted">Loading...</div>
        ) : statusError ? (
          <div className="alert alert-danger">{statusError}</div>
        ) : (
          <>
            <div className="card p-4 shadow-sm mb-4">
              <div className="d-flex align-items-center gap-3">
                <span className={`badge fs-6 bg-${enabled ? 'success' : 'secondary'}`}>
                  {enabled ? 'Enabled' : 'Disabled'}
                </span>
                <span className="text-muted">
                  {enabled
                    ? 'Your account is protected with two-factor authentication.'
                    : '2FA is not enabled. Enable it below to improve security.'}
                </span>
              </div>
            </div>

            {!enabled && (
              <div className="card p-4 shadow-sm mb-4">
                <h5 className="fw-semibold mb-3">Enable Two-Factor Authentication</h5>

                {enableSuccess && <div className="alert alert-success">{enableSuccess}</div>}
                {enableError && <div className="alert alert-danger">{enableError}</div>}

                {!otpSent ? (
                  <>
                    <p className="text-muted mb-3">
                      We will send a 6-digit code to your registered email address. Enter it below to confirm.
                    </p>
                    <button
                      className="btn btn-primary"
                      onClick={handleSendOtp}
                      disabled={sendingOtp}
                    >
                      {sendingOtp ? 'Sending...' : 'Send Verification Code'}
                    </button>
                  </>
                ) : (
                  <form onSubmit={handleEnable}>
                    <div className="alert alert-info">
                      A verification code has been sent to your email. It expires in 5 minutes.
                    </div>
                    <div className="mb-3">
                      <label className="form-label">Verification Code</label>
                      <input
                        className="form-control"
                        type="text"
                        inputMode="numeric"
                        pattern="\d{6}"
                        maxLength={6}
                        value={otp}
                        onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                        placeholder="000000"
                        required
                      />
                    </div>
                    <div className="d-flex gap-2">
                      <button className="btn btn-success" disabled={enabling}>
                        {enabling ? 'Enabling...' : 'Enable 2FA'}
                      </button>
                      <button
                        type="button"
                        className="btn btn-link"
                        onClick={handleSendOtp}
                        disabled={sendingOtp}
                      >
                        Resend code
                      </button>
                    </div>
                  </form>
                )}
              </div>
            )}

            {enabled && (
              <div className="card p-4 shadow-sm border-danger">
                <h5 className="fw-semibold mb-3 text-danger">Disable Two-Factor Authentication</h5>

                {disableSuccess && <div className="alert alert-success">{disableSuccess}</div>}
                {disableError && <div className="alert alert-danger">{disableError}</div>}

                <p className="text-muted mb-3">
                  Enter your password to confirm you want to disable 2FA.
                </p>
                <form onSubmit={handleDisable}>
                  <div className="mb-3">
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
                  <button className="btn btn-danger" disabled={disabling}>
                    {disabling ? 'Disabling...' : 'Disable 2FA'}
                  </button>
                </form>
              </div>
            )}
          </>
        )}
      </main>
    </>
  );
}
