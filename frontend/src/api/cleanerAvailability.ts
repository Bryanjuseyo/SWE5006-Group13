import { apiRequest } from './client';
import { getToken } from '../auth/storage';

export type AvailabilitySlot = {
  id: number;
  cleaner_profile_id: number;
  start_date: string;
  end_date: string;
  start_time: string | null;
  end_time: string | null;
};

export type AddAvailabilityPayload = {
  start_date: string;
  end_date: string;
  start_time?: string;
  end_time?: string;
};

export async function getAvailability() {
  return apiRequest<{ availability: AvailabilitySlot[] }>('/api/cleaner/availability', {
    token: getToken(),
  });
}

export async function addAvailability(payload: AddAvailabilityPayload) {
  return apiRequest<{ message: string; availability: AvailabilitySlot }>('/api/cleaner/availability', {
    method: 'POST',
    token: getToken(),
    body: payload,
  });
}

export async function updateAvailability(id: number, payload: AddAvailabilityPayload) {
  return apiRequest<{ message: string; availability: AvailabilitySlot }>(`/api/cleaner/availability/${id}`, {
    method: 'PUT',
    token: getToken(),
    body: payload,
  });
}

export async function deleteAvailability(id: number) {
  return apiRequest<{ message: string }>(`/api/cleaner/availability/${id}`, {
    method: 'DELETE',
    token: getToken(),
  });
}
