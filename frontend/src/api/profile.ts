import { apiRequest } from './client';
import { getToken } from '../auth/storage';

export type UserProfile = {
  id: number;
  user_id: number;
  first_name: string;
  last_name: string;
  phone?: string | null;
  address?: string | null;
  city?: string | null;
};

export type GetProfileResponse = {
  email: string;
  role: string;
  created_at: string;
  profile: UserProfile | null;
};

export async function getMyProfile() {
  return apiRequest<GetProfileResponse>('/api/profile', {
    method: 'GET',
    token: getToken(),
  });
}

export type UpdateProfileRequest = Partial<Pick<UserProfile, 'first_name' | 'last_name' | 'phone' | 'address' | 'city'>>;

export async function updateMyProfile(body: UpdateProfileRequest) {
  return apiRequest<{ message: string; profile: UserProfile }>('/api/profile', {
    method: 'PUT',
    token: getToken(),
    body,
  });
}