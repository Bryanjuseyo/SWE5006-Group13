import { apiRequest } from './client';

// =============================================
// TYPES
// =============================================

export type JobStatus = 'pending' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled';
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

export type UpdateJobRequestPayload = Partial<CreateJobRequestPayload>;

export type JobRequestResponse = {
  message: string;
  job_request: JobRequest;
};

export type JobRequestListResponse = {
  job_requests: JobRequest[];
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
  status?: JobStatus
): Promise<JobRequestListResponse> {
  const query = status ? `?status=${status}` : '';
  return apiRequest<JobRequestListResponse>(`/api/job-requests/${query}`, {
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

