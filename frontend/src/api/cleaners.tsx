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

export async function listCleaners() {
  return apiRequest<{ cleaners: CleanerListItem[] }>('/api/cleaner/list', {
    method: 'GET',
    token: getToken(),
  });
}