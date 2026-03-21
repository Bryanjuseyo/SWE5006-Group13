import { apiRequest } from './client';
import type { JobRequest, JobStatus } from './job_requests';

// =============================================
// TYPES
// =============================================

export type UserProfile = {
  id: number;
  user_id: number;
  first_name: string;
  last_name: string;
  phone: string | null;
  address: string | null;
  city: string | null;
};

export type AdminUser = {
  id: number;
  email: string;
  role: string;
  is_banned: boolean;
  banned_at: string | null;
  ban_reason: string | null;
  created_at: string;
  last_login_at: string | null;
  profile: UserProfile | null;
};

export type DashboardStats = {
  users: {
    total: number;
    end_users: number;
    cleaners: number;
    administrators: number;
    banned: number;
  };
  jobs: {
    total: number;
    pending: number;
    confirmed: number;
    in_progress: number;
    completed: number;
    cancelled: number;
    rejected: number;
  };
};

export type CleanerMatch = {
  cleaner_id: number;
  email: string;
  name: string;
  service_type: string;
  hourly_rate: number | null;
  years_experience: number;
  score: number;
};

// =============================================
// DASHBOARD
// =============================================

export async function getAdminStats(token: string): Promise<DashboardStats> {
  return apiRequest<DashboardStats>('/api/admin/stats', { token });
}

// =============================================
// USER MANAGEMENT
// =============================================

export async function getAdminUsers(
  token: string,
  params?: { role?: string; banned?: string; search?: string }
): Promise<{ users: AdminUser[] }> {
  const query = new URLSearchParams();
  if (params?.role) query.set('role', params.role);
  if (params?.banned) query.set('banned', params.banned);
  if (params?.search) query.set('search', params.search);
  const qs = query.toString();
  return apiRequest<{ users: AdminUser[] }>(`/api/admin/users${qs ? `?${qs}` : ''}`, { token });
}

export async function banUser(
  userId: number,
  token: string,
  reason?: string
): Promise<{ message: string; user: AdminUser }> {
  return apiRequest<{ message: string; user: AdminUser }>(`/api/admin/users/${userId}/ban`, {
    method: 'PATCH',
    body: reason ? { reason } : {},
    token,
  });
}

export async function unbanUser(
  userId: number,
  token: string
): Promise<{ message: string; user: AdminUser }> {
  return apiRequest<{ message: string; user: AdminUser }>(`/api/admin/users/${userId}/unban`, {
    method: 'PATCH',
    body: {},
    token,
  });
}

// =============================================
// BOOKING MANAGEMENT
// =============================================

export async function getAdminBookings(
  token: string,
  params?: { status?: string; search?: string }
): Promise<{ job_requests: JobRequest[] }> {
  const query = new URLSearchParams();
  if (params?.status) query.set('status', params.status);
  if (params?.search) query.set('search', params.search);
  const qs = query.toString();
  return apiRequest<{ job_requests: JobRequest[] }>(`/api/admin/bookings${qs ? `?${qs}` : ''}`, {
    token,
  });
}

export async function rejectBooking(
  jobRequestId: number,
  token: string,
  reason?: string
): Promise<{ message: string; job_request: JobRequest }> {
  return apiRequest<{ message: string; job_request: JobRequest }>(
    `/api/admin/bookings/${jobRequestId}/reject`,
    {
      method: 'PATCH',
      body: reason ? { reason } : {},
      token,
    }
  );
}

// =============================================
// CLEANER MATCHING
// =============================================

export async function getMatchingCleaners(
  jobRequestId: number,
  token: string
): Promise<{ job_request_id: number; matches: CleanerMatch[] }> {
  return apiRequest<{ job_request_id: number; matches: CleanerMatch[] }>(
    `/api/job-requests/${jobRequestId}/match`,
    { token }
  );
}

export async function autoAssignCleaner(
  jobRequestId: number,
  token: string
): Promise<{ message: string; job_request: JobRequest; assigned_cleaner: CleanerMatch }> {
  return apiRequest<{ message: string; job_request: JobRequest; assigned_cleaner: CleanerMatch }>(
    `/api/job-requests/${jobRequestId}/auto-assign`,
    { method: 'POST', body: {}, token }
  );
}
