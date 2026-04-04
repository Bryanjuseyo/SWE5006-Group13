import { useEffect, useMemo, useState } from 'react';
import Navbar from '../components/Navbar';
import { listCleaners } from '../api/cleaners';
import type { CleanerListItem } from '../api/cleaners';

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export default function ViewCleanersPage() {
  const [cleaners, setCleaners] = useState<CleanerListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState('');

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await listCleaners();
        if (mounted) setCleaners(res.cleaners);
      } catch (e: unknown) {
        if (mounted) setError(getErrorMessage(e, 'Failed to load cleaners'));
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (!s) return cleaners;
    return cleaners.filter((c) => {
      const name = `${c.first_name} ${c.last_name}`.toLowerCase();
      const email = (c.email || '').toLowerCase();
      const city = (c.city || '').toLowerCase();
      const serviceType = (c.cleaner_profile?.service_type || '').toLowerCase();
      return name.includes(s) || email.includes(s) || city.includes(s) || serviceType.includes(s);
    });
  }, [cleaners, q]);

  return (
    <>
      <Navbar />
      <div className="container py-4">
        <div className="d-flex align-items-center justify-content-between mb-3">
          <h3 className="m-0">View Cleaners</h3>
          <div style={{ maxWidth: 360 }} className="w-100">
            <input
              className="form-control"
              placeholder="Search by name, email, city, service type..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
        </div>

        {loading && <div className="alert alert-info">Loading cleaners...</div>}
        {error && <div className="alert alert-danger">{error}</div>}

        {!loading && !error && filtered.length === 0 && (
          <div className="alert alert-secondary">No cleaners found.</div>
        )}

        <div className="row g-3">
          {filtered.map((c) => (
            <div className="col-12 col-md-6 col-lg-4" key={c.user_id}>
              <div className="card h-100 shadow-sm">
                <div className="card-body">
                  <div className="d-flex justify-content-between align-items-start">
                    <div>
                      <h5 className="card-title mb-1">
                        {c.first_name} {c.last_name}
                      </h5>
                      <div className="text-muted small">{c.email}</div>
                      {c.city && <div className="text-muted small">{c.city}</div>}
                    </div>
                    <span className="badge text-bg-light border">
                      {c.cleaner_profile?.service_type === 'full' ? 'Full' : 'Partial'}
                    </span>
                  </div>

                  <hr />

                  <div className="d-flex justify-content-between">
                    <div>
                      <div className="text-muted small">Hourly Rate</div>
                      <div>
                        {c.cleaner_profile?.hourly_rate != null ? `$${c.cleaner_profile.hourly_rate}` : '-'}
                      </div>
                    </div>
                    <div className="text-end">
                      <div className="text-muted small">Experience</div>
                      <div>{c.cleaner_profile?.years_experience ?? 0} yrs</div>
                    </div>
                  </div>

                  {c.cleaner_profile?.offered_services?.length ? (
                    <div className="mt-3">
                      <div className="text-muted small mb-1">Offered Services</div>
                      <div className="d-flex flex-wrap gap-1">
                        {c.cleaner_profile.offered_services.slice(0, 6).map((s) => (
                          <span key={s.id} className="badge text-bg-secondary">
                            {s.cleaning_service?.name}
                          </span>
                        ))}
                        {c.cleaner_profile.offered_services.length > 6 && (
                          <span className="badge text-bg-light border">
                            +{c.cleaner_profile.offered_services.length - 6}
                          </span>
                        )}
                      </div>
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}