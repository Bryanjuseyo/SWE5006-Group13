import { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import { getCleanerProfile, updateCleanerProfile } from '../api/cleanerProfile';

export default function CleanerProfilePage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [serviceType, setServiceType] = useState<'partial' | 'full'>('partial');
  const [hourlyRate, setHourlyRate] = useState<string>('');
  const [years, setYears] = useState<string>('0');

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const res = await getCleanerProfile();
      const p = res.profile;

      if (p) {
        setServiceType(p.service_type);
        setHourlyRate(p.hourly_rate != null ? String(p.hourly_rate) : '');
        setYears(String(p.years_experience ?? 0));
      }
    } catch (e: any) {
      setError(e?.message || 'Failed to load cleaner profile.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const yearsInt = parseInt(years, 10);
    if (Number.isNaN(yearsInt) || yearsInt < 0) {
      setError('Years of experience must be a non-negative integer.');
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
      setSaving(true);
      await updateCleanerProfile({
        service_type: serviceType,
        hourly_rate: rateNum,
        years_experience: yearsInt,
      });
      setSuccess('Cleaner profile saved.');
      await load();
    } catch (e: any) {
      setError(e?.message || 'Failed to save cleaner profile.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="container py-5" style={{ maxWidth: 720 }}>
        <h1 className="h3 fw-bold mb-3">Cleaner Profile</h1>

        {loading ? (
          <div className="text-muted">Loading...</div>
        ) : (
          <>
            {error && <div className="alert alert-danger">{error}</div>}
            {success && <div className="alert alert-success">{success}</div>}

            <form onSubmit={onSave} className="card p-4 shadow-sm">
              <div className="mb-3">
                <label className="form-label">Service Type</label>
                <select
                  className="form-select"
                  value={serviceType}
                  onChange={(e) => setServiceType(e.target.value as 'partial' | 'full')}
                >
                  <option value="partial">Partial</option>
                  <option value="full">Full</option>
                </select>
              </div>

              <div className="row g-3">
                <div className="col-md-6">
                  <label className="form-label">Hourly Rate (SGD)</label>
                  <input
                    className="form-control"
                    value={hourlyRate}
                    onChange={(e) => setHourlyRate(e.target.value)}
                    placeholder="e.g. 25.50"
                  />
                </div>

                <div className="col-md-6">
                  <label className="form-label">Years of Experience</label>
                  <input
                    className="form-control"
                    value={years}
                    onChange={(e) => setYears(e.target.value)}
                    placeholder="e.g. 2"
                  />
                </div>
              </div>

              <button className="btn btn-primary mt-4" disabled={saving}>
                {saving ? 'Saving...' : 'Save Cleaner Profile'}
              </button>
            </form>
          </>
        )}
      </main>
    </>
  );
}