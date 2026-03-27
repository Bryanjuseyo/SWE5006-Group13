import { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import { getMyProfile, updateMyProfile } from '../api/profile';

function isValidPhone(phone: string) {
  return /^[89]\d{7}$/.test(phone);
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export default function ProfilePage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [email, setEmail] = useState('');
  const [role, setRole] = useState('');
  const [createdAt, setCreatedAt] = useState('');

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [city, setCity] = useState('');

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const res = await getMyProfile();
      setEmail(res.email);
      setRole(res.role);
      setCreatedAt(res.created_at);

      const p = res.profile;
      setFirstName(p?.first_name ?? '');
      setLastName(p?.last_name ?? '');
      setPhone(p?.phone ?? '');
      setAddress(p?.address ?? '');
      setCity(p?.city ?? '');
    } catch (e: unknown) {
      setError(getErrorMessage(e, 'Failed to load profile.'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!firstName.trim() || !lastName.trim()) {
      setError('First name and last name are required.');
      return;
    }
    if (phone.trim() && !isValidPhone(phone.trim())) {
      setError('Phone number must start with 8 or 9 and be 8 digits long.');
      return;
    }

    try {
      setSaving(true);
      await updateMyProfile({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        phone: phone.trim() ? phone.trim() : null,
        address: address.trim() ? address.trim() : null,
        city: city.trim() ? city.trim() : null,
      });
      setSuccess('Profile saved.');
      await load();
    } catch (e: unknown) {
      setError(getErrorMessage(e, 'Failed to save profile.'));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="container py-5" style={{ maxWidth: 720 }}>
        <h1 className="h3 fw-bold mb-3">My Profile</h1>

        {loading ? (
          <div className="text-muted">Loading...</div>
        ) : (
          <>
            {error && <div className="alert alert-danger">{error}</div>}
            {success && <div className="alert alert-success">{success}</div>}

            <div className="card p-4 shadow-sm mb-4">
              <div className="row g-3">
                <div className="col-md-6">
                  <div className="text-muted small">Email</div>
                  <div className="fw-semibold">{email}</div>
                </div>
                <div className="col-md-3">
                  <div className="text-muted small">Role</div>
                  <div className="fw-semibold">{role}</div>
                </div>
                <div className="col-md-3">
                  <div className="text-muted small">Created</div>
                  <div className="fw-semibold">{new Date(createdAt).toLocaleDateString()}</div>
                </div>
              </div>
            </div>

            <form onSubmit={onSave} className="card p-4 shadow-sm">
              <div className="row g-3">
                <div className="col-md-6">
                  <label className="form-label">First Name</label>
                  <input
                    className="form-control"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                  />
                </div>

                <div className="col-md-6">
                  <label className="form-label">Last Name</label>
                  <input
                    className="form-control"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                  />
                </div>

                <div className="col-md-6">
                  <label className="form-label">Phone</label>
                  <input
                    className="form-control"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="e.g. 91234567"
                  />
                  <div className="form-text">8 digits, starts with 8 or 9</div>
                </div>

                <div className="col-md-6">
                  <label className="form-label">City</label>
                  <input
                    className="form-control"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    placeholder="e.g. Singapore"
                  />
                </div>

                <div className="col-12">
                  <label className="form-label">Address</label>
                  <textarea
                    className="form-control"
                    rows={3}
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                  />
                </div>
              </div>

              <button className="btn btn-primary mt-4" disabled={saving}>
                {saving ? 'Saving...' : 'Save Profile'}
              </button>
            </form>
          </>
        )}
      </main>
    </>
  );
}