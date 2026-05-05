import type { CleanerListItem } from '../api/cleaners';
import type { PreferredCleanerId } from '../hooks/useEligibleCleaners';

type PreferredCleanerSelectProps = {
  cleaners: CleanerListItem[];
  value: PreferredCleanerId;
  canLoadCleaners: boolean;
  emptyOptionLabel: string;
  helperText: string;
  onChange: (value: PreferredCleanerId) => void;
};

export default function PreferredCleanerSelect({
  cleaners,
  value,
  canLoadCleaners,
  emptyOptionLabel,
  helperText,
  onChange,
}: PreferredCleanerSelectProps) {
  const placeholder = !canLoadCleaners
    ? 'Select service type and date first'
    : cleaners.length === 0
      ? 'No eligible cleaners available'
      : emptyOptionLabel;

  return (
    <>
      <select
        className="form-select"
        value={value}
        disabled={!canLoadCleaners}
        onChange={(e) => {
          const selected = e.target.value;
          onChange(selected === '' ? '' : Number(selected));
        }}
      >
        <option value="">{placeholder}</option>
        {cleaners.map((cleaner) => (
          <option key={cleaner.user_id} value={cleaner.user_id}>
            {cleaner.first_name} {cleaner.last_name} - {cleaner.cleaner_profile.service_type} -{' '}
            {cleaner.cleaner_profile.hourly_rate != null
              ? `$${cleaner.cleaner_profile.hourly_rate}/hr`
              : 'Rate N/A'}{' '}
            - {cleaner.cleaner_profile.years_experience} yrs
          </option>
        ))}
      </select>
      <div className="form-text">{helperText}</div>
    </>
  );
}
