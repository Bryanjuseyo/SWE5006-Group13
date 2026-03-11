import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { register, type UserRole } from '../api/auth';
import { updateMyProfile } from '../api/profile';
import { updateCleanerProfile } from '../api/cleanerProfile';
import { setAuth } from '../auth/storage';

function isValidEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function isValidPassword(pw: string) {
  if (pw.length < 8) return false;
  return /[A-Za-z]/.test(pw) && /\d/.test(pw);
}

function isValidPhone(phone: string) {
  return /^[89]\d{7}$/.test(phone);
}

export default function RegisterPage() {
  const navigate = useNavigate();

  // Step tracking (step 3 only shown for cleaners)
  const [step, setStep] = useState<1 | 2 | 3>(1);

  // Step 1 fields
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('end_user');

  // Step 2 fields
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [city, setCity] = useState('');

  // Step 3 fields (cleaner only)
  const [serviceType, setServiceType] = useState<'partial' | 'full'>('partial');
  const [hourlyRate, setHourlyRate] = useState('');
  const [yearsExperience, setYearsExperience] = useState('0');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onStep1Submit(e: React.FormEvent) {
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
      const res = await register({ email: eTrim, password, role });
      setAuth(res.token, res.user);
      setStep(2);
    } catch (err: any) {
      setError(err?.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  }

  async function onStep2Submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!firstName.trim() || !lastName.trim()) {
      setError('First name and last name are required.');
      return;
    }
    if (phone && !isValidPhone(phone)) {
      setError('Phone must be 8 digits and start with 8 or 9.');
      return;
    }

    try {
      setLoading(true);
      await updateMyProfile({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        phone: phone || undefined,
        address: address.trim() || undefined,
        city: city.trim() || undefined,
      });
      if (role === 'cleaner') {
        setStep(3);
      } else {
        navigate('/dashboard', { replace: true });
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to save profile.');
    } finally {
      setLoading(false);
    }
  }

  async function onStep3Submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const yearsInt = parseInt(yearsExperience, 10);
    if (Number.isNaN(yearsInt) || yearsInt < 0) {
      setError('Years of experience must be a non-negative number.');
      return;
    }

    let rateNum: number | null = null;
    if (hourlyRate.trim()) {
      rateNum = Number(hourlyRate);
      if (Number.isNaN(rateNum) || rateNum < 0) {
        setError('Hourly rate must be a non-negative number.');
        return;
      }
    }

    try {
      setLoading(true);
      await updateCleanerProfile({
        service_type: serviceType,
        hourly_rate: rateNum,
        years_experience: yearsInt,
      });
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      setError(err?.message || 'Failed to save cleaner profile.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="container py-5" style={{ maxWidth: 520 }}>
        <h1 className="h3 fw-bold mb-1">Create an account</h1>

        {/* Step indicator */}
        <div className="d-flex align-items-center gap-2 mb-4">
          <span className={`badge rounded-pill ${step === 1 ? 'bg-primary' : 'bg-success'}`}>
            {step === 1 ? '1' : '✓'}
          </span>
          <span className={step === 1 ? 'fw-semibold' : 'text-muted'}>Account info</span>
          <span className="text-muted mx-1">→</span>
          <span className={`badge rounded-pill ${step === 2 ? 'bg-primary' : step > 2 ? 'bg-success' : 'bg-secondary'}`}>
            {step > 2 ? '✓' : '2'}
          </span>
          <span className={step === 2 ? 'fw-semibold' : 'text-muted'}>Your profile</span>
          {(role === 'cleaner' || step === 3) && (
            <>
              <span className="text-muted mx-1">→</span>
              <span className={`badge rounded-pill ${step === 3 ? 'bg-primary' : 'bg-secondary'}`}>3</span>
              <span className={step === 3 ? 'fw-semibold' : 'text-muted'}>Cleaner details</span>
            </>
          )}
        </div>

        {error && <div className="alert alert-danger">{error}</div>}

        {step === 1 && (
          <form onSubmit={onStep1Submit} className="card p-4 shadow-sm">
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
              {loading ? 'Creating account...' : 'Next: Create profile'}
            </button>

            <div className="text-center mt-3">
              <span className="text-muted">Already have an account?</span>{' '}
              <Link to="/login">Login</Link>
            </div>
          </form>
        )}

        {step === 2 && (
          <form onSubmit={onStep2Submit} className="card p-4 shadow-sm">
            <p className="text-muted mb-3">Tell us a bit about yourself to complete your account setup.</p>

            <div className="row g-3 mb-3">
              <div className="col-6">
                <label className="form-label">First name <span className="text-danger">*</span></label>
                <input
                  className="form-control"
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="Jane"
                  required
                />
              </div>
              <div className="col-6">
                <label className="form-label">Last name <span className="text-danger">*</span></label>
                <input
                  className="form-control"
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Doe"
                  required
                />
              </div>
            </div>

            <div className="mb-3">
              <label className="form-label">Phone <span className="text-muted">(optional)</span></label>
              <input
                className="form-control"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="8-digit SG number (starts with 8 or 9)"
              />
            </div>

            <div className="mb-3">
              <label className="form-label">Address <span className="text-muted">(optional)</span></label>
              <input
                className="form-control"
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="123 Orchard Rd"
              />
            </div>

            <div className="mb-4">
              <label className="form-label">City <span className="text-muted">(optional)</span></label>
              <input
                className="form-control"
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="Singapore"
              />
            </div>

            <button className="btn btn-success w-100" disabled={loading}>
              {loading ? 'Saving profile...' : role === 'cleaner' ? 'Next: Cleaner details' : 'Complete registration'}
            </button>
          </form>
        )}

        {step === 3 && (
          <form onSubmit={onStep3Submit} className="card p-4 shadow-sm">
            <p className="text-muted mb-3">Set up your cleaner profile so end users can find and book you.</p>

            <div className="mb-3">
              <label className="form-label">Service Type <span className="text-danger">*</span></label>
              <select
                className="form-select"
                value={serviceType}
                onChange={(e) => setServiceType(e.target.value as 'partial' | 'full')}
              >
                <option value="partial">Partial</option>
                <option value="full">Full</option>
              </select>
            </div>

            <div className="row g-3 mb-4">
              <div className="col-md-6">
                <label className="form-label">Hourly Rate (SGD) <span className="text-muted">(optional)</span></label>
                <input
                  className="form-control"
                  type="number"
                  min="0"
                  step="0.01"
                  value={hourlyRate}
                  onChange={(e) => setHourlyRate(e.target.value)}
                  placeholder="e.g. 25.50"
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">Years of Experience <span className="text-danger">*</span></label>
                <input
                  className="form-control"
                  type="number"
                  min="0"
                  value={yearsExperience}
                  onChange={(e) => setYearsExperience(e.target.value)}
                  placeholder="e.g. 2"
                />
              </div>
            </div>

            <button className="btn btn-success w-100" disabled={loading}>
              {loading ? 'Saving...' : 'Complete registration'}
            </button>
          </form>
        )}
      </main>
    </>
  );
}
