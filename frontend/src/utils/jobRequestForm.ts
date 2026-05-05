import type { ServiceType } from '../api/job_requests';

type JobRequestFormValues = {
  title: string;
  serviceType: ServiceType | '';
  location: string;
  preferredDate: string;
  preferredTimeStart: string;
  preferredTimeEnd: string;
  today: string;
  currentTime: string;
  rejectPastDate?: boolean;
};

export function getJobRequestFormError({
  title,
  serviceType,
  location,
  preferredDate,
  preferredTimeStart,
  preferredTimeEnd,
  today,
  currentTime,
  rejectPastDate = false,
}: JobRequestFormValues): string | null {
  if (!title.trim()) return 'Title is required.';
  if (!serviceType) return 'Service type is required.';
  if (!location.trim()) return 'Location is required.';
  if (!preferredDate) return 'Preferred date is required.';
  if (rejectPastDate && preferredDate < today) return 'Preferred date cannot be in the past.';

  if (preferredTimeStart && preferredDate === today && preferredTimeStart < currentTime) {
    return 'Start time cannot be in the past.';
  }

  if (preferredTimeStart && preferredTimeEnd && preferredTimeEnd <= preferredTimeStart) {
    return 'End time must be strictly after start time.';
  }

  return null;
}
