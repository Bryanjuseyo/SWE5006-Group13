import { apiRequest } from './client';

// =============================================
// TYPES
// =============================================

export type JobStatus = 'pending' | 'confirmed' | 'in_progress' | 'cleaner_completed' | 'completed' | 'cancelled' | 'rejected';
export type ServiceType = 'partial' | 'full';

export type JobRequest = {
  id: number;
  end_user_id: number;
  cleaner_id: number | null;
  title: string;
  description: string | null;
  service_type: ServiceType | null;
  location: string | null;
  preferred_date: string | null;
  preferred_time_start: string | null;
  preferred_time_end: string | null;
  status: JobStatus;
  priority_window_end: string | null;
  is_in_priority_window: boolean;
  created_at: string;
  updated_at: string;
  end_user: {
    id: number;
    email: string;
    role: string;
    created_at: string;
  } | null;
  cleaner: {
    id: number;
    email: string;
    role: string;
    created_at: string;
  } | null;
};

// =============================================
// REQUEST/RESPONSE TYPES
// =============================================

export type CreateJobRequestPayload = {
  title: string;
  description?: string;
  service_type: ServiceType;
  location: string;
  preferred_date: string;
  preferred_time_start?: string;
  preferred_time_end?: string;
  cleaner_id?: number | null;
};

export type UpdateJobRequestPayload = Partial<Omit<CreateJobRequestPayload, 'preferred_time_start' | 'preferred_time_end'>> & {
  preferred_time_start?: string | null;
  preferred_time_end?: string | null;
};

export type JobRequestResponse = {
  message: string;
  job_request: JobRequest;
};

export type PaginationMeta = {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
  has_prev: boolean;
  has_next: boolean;
};

export type JobRequestListResponse = {
  job_requests: JobRequest[];
  pagination: PaginationMeta;
};

export type CleanerScheduleResponse = {
  schedule: JobRequest[];
  pagination: PaginationMeta;
};

// =============================================
// API FUNCTIONS
// =============================================

/**
 * Create a new job request
 */
export async function createJobRequest(
  payload: CreateJobRequestPayload,
  token: string
): Promise<JobRequestResponse> {
  return apiRequest<JobRequestResponse>('/api/job-requests/', {
    method: 'POST',
    body: payload,
    token,
  });
}

/**
 * Get all job requests for the current user
 */
export async function getJobRequests(
  token: string,
  status?: JobStatus,
  page?: number,
  perPage?: number
): Promise<JobRequestListResponse> {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (page) params.set('page', String(page));
  if (perPage) params.set('per_page', String(perPage));
  const query = params.toString();
  return apiRequest<JobRequestListResponse>(`/api/job-requests/${query ? `?${query}` : ''}`, {
    token,
  });
}

/**
 * Get a single job request by ID
 */
export async function getJobRequest(
  id: number,
  token: string
): Promise<{ job_request: JobRequest }> {
  return apiRequest<{ job_request: JobRequest }>(`/api/job-requests/${id}`, {
    token,
  });
}

/**
 * Update a job request
 */
export async function updateJobRequest(
  id: number,
  payload: UpdateJobRequestPayload,
  token: string
): Promise<JobRequestResponse> {
  return apiRequest<JobRequestResponse>(`/api/job-requests/${id}`, {
    method: 'PUT',
    body: payload,
    token,
  });
}

/**
 * Delete a job request
 */
export async function deleteJobRequest(
  id: number,
  token: string
): Promise<{ message: string }> {
  return apiRequest<{ message: string }>(`/api/job-requests/${id}`, {
    method: 'DELETE',
    token,
  });
}

/**
 * Update job request status
 */
export async function updateJobStatus(
  id: number,
  status: JobStatus,
  token: string
): Promise<JobRequestResponse> {
  return apiRequest<JobRequestResponse>(`/api/job-requests/${id}/status`, {
    method: 'PATCH',
    body: { status },
    token,
  });
}

/**
 * Get cleaner's upcoming schedule (confirmed / in_progress jobs)
 */
export async function getCleanerSchedule(
  token: string,
  page?: number,
  perPage?: number
): Promise<CleanerScheduleResponse> {
  const params = new URLSearchParams();
  if (page) params.set('page', String(page));
  if (perPage) params.set('per_page', String(perPage));
  const query = params.toString();
  return apiRequest<CleanerScheduleResponse>(`/api/cleaner/schedule${query ? `?${query}` : ''}`, {
    token,
  });
}

/**
 * Get open jobs available for the cleaner to accept
 */
export async function getAvailableJobs(
  token: string,
  page?: number,
  perPage?: number
): Promise<JobRequestListResponse> {
  const params = new URLSearchParams();
  if (page) params.set('page', String(page));
  if (perPage) params.set('per_page', String(perPage));
  const query = params.toString();
  return apiRequest<JobRequestListResponse>(
    `/api/cleaner/available-jobs${query ? `?${query}` : ''}`,
    { token }
  );
}

