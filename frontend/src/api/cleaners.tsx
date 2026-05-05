import { apiRequest } from './client';
import { getToken } from '../auth/storage';

export type CleanerListItem = {
  user_id: number;
  email: string;
  first_name: string;
  last_name: string;
  city?: string | null;
  cleaner_profile: {
    id: number;
    user_id: number;
    service_type: 'partial' | 'full';
    hourly_rate?: number | null;
    years_experience: number;
    offered_services?: Array<{ id: number; cleaning_service: { id: number; name: string; description?: string | null }; custom_price?: number | null }>;
    availability?: Array<{ id: number; cleaner_profile_id: number; start_date: string; end_date: string; start_time?: string | null; end_time?: string | null }>;
  };
};

export type ListCleanersParams = {
  service_type?: 'partial' | 'full';
  preferred_date?: string;
  preferred_time_start?: string;
  preferred_time_end?: string;
  exclude_job_request_id?: number;
};

export async function listCleaners(params?: ListCleanersParams) {
  const query = new URLSearchParams();
  if (params?.service_type) query.set('service_type', params.service_type);
  if (params?.preferred_date) query.set('preferred_date', params.preferred_date);
  if (params?.preferred_time_start) query.set('preferred_time_start', params.preferred_time_start);
  if (params?.preferred_time_end) query.set('preferred_time_end', params.preferred_time_end);
  if (params?.exclude_job_request_id) query.set('exclude_job_request_id', String(params.exclude_job_request_id));

  const qs = query.toString();
  return apiRequest<{ cleaners: CleanerListItem[] }>(`/api/cleaner/list${qs ? `?${qs}` : ''}`, {
    method: 'GET',
    token: getToken(),
  });
}
