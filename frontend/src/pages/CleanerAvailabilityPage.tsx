import { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import {
  getAvailability,
  addAvailability,
  updateAvailability,
  deleteAvailability,
  type AvailabilitySlot,
} from '../api/cleanerAvailability';

function formatDate(d: string) {
  return new Date(d + 'T00:00:00').toLocaleDateString(undefined, {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatTime(t: string | null) {
  if (!t) return null;
  const [h, m] = t.split(':');
  const date = new Date();
  date.setHours(Number(h), Number(m));
  return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export default function CleanerAvailabilityPage() {
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // null = adding new, number = editing existing slot id
  const [editingId, setEditingId] = useState<number | null>(null);

  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await getAvailability();
      setSlots(res.availability);
    } catch (e: unknown) {
      setError(getErrorMessage(e, 'Failed to load availability.'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  function resetForm() {
    setEditingId(null);
    setStartDate('');
    setEndDate('');
    setStartTime('');
    setEndTime('');
    setError(null);
    setSuccess(null);
  }

  function handleEditClick(slot: AvailabilitySlot) {
    setEditingId(slot.id);
    setStartDate(slot.start_date);
    setEndDate(slot.end_date);
    setStartTime(slot.start_time ? slot.start_time.slice(0, 5) : '');
    setEndTime(slot.end_time ? slot.end_time.slice(0, 5) : '');
    setError(null);
    setSuccess(null);
  }

  function validate() {
    if (!startDate || !endDate) {
      setError('Start date and end date are required.');
      return false;
    }
    if (endDate < startDate) {
      setError('End date must be on or after start date.');
      return false;
    }
    if (startTime && endTime && endTime <= startTime) {
      setError('End time must be after start time.');
      return false;
    }
    return true;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!validate()) return;

    const payload = {
      start_date: startDate,
      end_date: endDate,
      start_time: startTime || undefined,
      end_time: endTime || undefined,
    };

    try {
      setSaving(true);
      if (editingId !== null) {
        await updateAvailability(editingId, payload);
        setSuccess('Availability slot updated.');
      } else {
        await addAvailability(payload);
        setSuccess('Availability slot added.');
      }
      resetForm();
      await load();
    } catch (e: unknown) {
      setError(getErrorMessage(e, 'Failed to save availability slot.'));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Remove this availability slot?')) return;
    setError(null);
    setSuccess(null);
    try {
      await deleteAvailability(id);
      setSlots((prev) => prev.filter((s) => s.id !== id));
      setSuccess('Availability slot removed.');
      if (editingId === id) resetForm();
    } catch (e: unknown) {
      setError(getErrorMessage(e, 'Failed to remove slot.'));
    }
  }

  return (
    <>
      <Navbar />
      <main className="container py-5" style={{ maxWidth: 760 }}>
        <h1 className="h3 fw-bold mb-1">Availability Management</h1>
        <p className="text-muted mb-4">
          Set your available date ranges and optional time windows so clients know when you can work.
        </p>

        {error && <div className="alert alert-danger">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        <div className="card shadow-sm mb-5">
          <div className="card-header fw-semibold d-flex justify-content-between align-items-center">
            <span>{editingId !== null ? 'Edit Availability Slot' : 'Add Availability Slot'}</span>
            {editingId !== null && (
              <button className="btn btn-sm btn-outline-secondary" onClick={resetForm}>
                Cancel
              </button>
            )}
          </div>
          <div className="card-body">
            <form onSubmit={handleSubmit}>
              <div className="row g-3 mb-3">
                <div className="col-md-6">
                  <label className="form-label">
                    Start Date <span className="text-danger">*</span>
                  </label>
                  <input
                    type="date"
                    className="form-control"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    required
                  />
                </div>
                <div className="col-md-6">
                  <label className="form-label">
                    End Date <span className="text-danger">*</span>
                  </label>
                  <input
                    type="date"
                    className="form-control"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    required
                  />
                </div>
              </div>
              <div className="row g-3 mb-3">
                <div className="col-md-6">
                  <label className="form-label">
                    Start Time <span className="text-muted">(optional)</span>
                  </label>
                  <input
                    type="time"
                    className="form-control"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                  />
                </div>
                <div className="col-md-6">
                  <label className="form-label">
                    End Time <span className="text-muted">(optional)</span>
                  </label>
                  <input
                    type="time"
                    className="form-control"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                  />
                </div>
              </div>
              <button className="btn btn-primary" disabled={saving}>
                {saving ? 'Saving...' : editingId !== null ? 'Save Changes' : 'Add Slot'}
              </button>
            </form>
          </div>
        </div>

        <h2 className="h5 fw-semibold mb-3">Your Availability Slots</h2>
        {loading ? (
          <div className="text-center py-4">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
          </div>
        ) : slots.length === 0 ? (
          <div className="alert alert-info">No availability slots set. Add one above.</div>
        ) : (
          <div className="list-group">
            {slots.map((slot) => (
              <div
                key={slot.id}
                className={`list-group-item d-flex justify-content-between align-items-center ${editingId === slot.id ? 'list-group-item-warning' : ''
                  }`}
              >
                <div>
                  <span className="fw-medium">{formatDate(slot.start_date)}</span>
                  {slot.start_date !== slot.end_date && (
                    <>
                      {' '}
                      &rarr; <span className="fw-medium">{formatDate(slot.end_date)}</span>
                    </>
                  )}
                  {slot.start_time && (
                    <span className="ms-3 text-muted small">
                      {formatTime(slot.start_time)}
                      {slot.end_time && ` - ${formatTime(slot.end_time)}`}
                    </span>
                  )}
                </div>
                <div className="d-flex gap-2">
                  <button
                    className="btn btn-sm btn-outline-primary"
                    onClick={() => handleEditClick(slot)}
                    disabled={editingId === slot.id}
                  >
                    Edit
                  </button>
                  <button
                    className="btn btn-sm btn-outline-danger"
                    onClick={() => handleDelete(slot.id)}
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </>
  );
}