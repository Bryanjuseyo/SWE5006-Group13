import type { ServiceType } from '../api/job_requests';

type JobRequestFormFieldsProps = {
  title: string;
  description: string;
  serviceType: ServiceType | '';
  location: string;
  preferredDate: string;
  preferredTimeStart: string;
  preferredTimeEnd: string;
  today: string;
  currentTime: string;
  onTitleChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onServiceTypeChange: (value: ServiceType | '') => void;
  onLocationChange: (value: string) => void;
  onPreferredDateChange: (value: string) => void;
  onPreferredTimeStartChange: (value: string) => void;
  onPreferredTimeEndChange: (value: string) => void;
};

export default function JobRequestFormFields({
  title,
  description,
  serviceType,
  location,
  preferredDate,
  preferredTimeStart,
  preferredTimeEnd,
  today,
  currentTime,
  onTitleChange,
  onDescriptionChange,
  onServiceTypeChange,
  onLocationChange,
  onPreferredDateChange,
  onPreferredTimeStartChange,
  onPreferredTimeEndChange,
}: JobRequestFormFieldsProps) {
  return (
    <>
      <div className="mb-3">
        <label className="form-label">
          Title <span className="text-danger">*</span>
        </label>
        <input
          className="form-control"
          type="text"
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
          placeholder="e.g., Weekly house cleaning"
          required
        />
      </div>

      <div className="mb-3">
        <label className="form-label">Description</label>
        <textarea
          className="form-control"
          rows={3}
          value={description}
          onChange={(e) => onDescriptionChange(e.target.value)}
          placeholder="Describe your cleaning requirements..."
        />
      </div>

      <div className="row mb-3">
        <div className="col-md-6">
          <label className="form-label">
            Service Type <span className="text-danger">*</span>
          </label>
          <select
            className="form-select"
            value={serviceType}
            onChange={(e) => onServiceTypeChange(e.target.value as ServiceType | '')}
            required
          >
            <option value="">Select type...</option>
            <option value="partial">Partial Cleaning</option>
            <option value="full">Full Cleaning</option>
          </select>
        </div>
        <div className="col-md-6">
          <label className="form-label">
            Location <span className="text-danger">*</span>
          </label>
          <input
            className="form-control"
            type="text"
            value={location}
            onChange={(e) => onLocationChange(e.target.value)}
            placeholder="e.g., 123 Main St, Singapore"
            required
          />
        </div>
      </div>

      <div className="row mb-3">
        <div className="col-md-4">
          <label className="form-label">
            Preferred Date <span className="text-danger">*</span>
          </label>
          <input
            className="form-control"
            type="date"
            value={preferredDate}
            onChange={(e) => onPreferredDateChange(e.target.value)}
            min={today}
            required
          />
        </div>
        <div className="col-md-4">
          <label className="form-label">Start Time</label>
          <input
            className="form-control"
            type="time"
            value={preferredTimeStart}
            onChange={(e) => onPreferredTimeStartChange(e.target.value)}
            min={preferredDate === today ? currentTime : undefined}
          />
        </div>
        <div className="col-md-4">
          <label className="form-label">End Time</label>
          <input
            className="form-control"
            type="time"
            value={preferredTimeEnd}
            onChange={(e) => onPreferredTimeEndChange(e.target.value)}
            min={preferredTimeStart || undefined}
          />
        </div>
      </div>
    </>
  );
}
