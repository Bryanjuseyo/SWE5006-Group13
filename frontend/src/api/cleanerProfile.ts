import { apiRequest } from './client';
import { getToken } from '../auth/storage';

export type CleanerProfile = {
  id: number;
  user_id: number;
  service_type: 'partial' | 'full';
  hourly_rate?: number | null;
  years_experience: number;
};

export async function getCleanerProfile() {
  return apiRequest<{ profile: CleanerProfile | null }>('/api/cleaner/profile', {
    method: 'GET',
    token: getToken(),
  });
}

export type UpdateCleanerProfileRequest = Partial<Pick<CleanerProfile, 'service_type' | 'hourly_rate' | 'years_experience'>>;

export async function updateCleanerProfile(body: UpdateCleanerProfileRequest) {
  return apiRequest<{ message: string; profile: CleanerProfile }>('/api/cleaner/profile', {
    method: 'PUT',
    token: getToken(),
    body,
  });
}