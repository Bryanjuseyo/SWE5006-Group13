import { apiRequest } from './client';

export type UserRole = 'end_user' | 'cleaner' | 'administrator';

export type RegisterRequest = {
  email: string;
  password: string;
  role: UserRole;
  first_name: string;
  last_name: string;
  phone?: string;
  address?: string;
  city?: string;
  service_type?: 'partial' | 'full';
  hourly_rate?: number | null;
  years_experience?: number;
};

export type AuthUser = {
  id: number;
  email: string;
  role: UserRole;
  created_at: string;
  two_factor_enabled: boolean;
};

export type RegisterResponse = {
  message: string;
  requires_2fa: true;
  temp_token: string;
};

export async function register(req: RegisterRequest) {
  return apiRequest<RegisterResponse>('/api/auth/register', {
    method: 'POST',
    body: req,
  });
}

export type LoginRequest = { email: string; password: string };

export type LoginSuccessResponse = {
  message: string;
  token: string;
  user: AuthUser;
};

export type Login2FAResponse = {
  message: string;
  requires_2fa: true;
  temp_token: string;
};

export type LoginResponse = LoginSuccessResponse | Login2FAResponse;

export async function login(req: LoginRequest) {
  return apiRequest<LoginResponse>('/api/auth/login', {
    method: 'POST',
    body: req,
  });
}

// =============================================
// TWO-FACTOR AUTHENTICATION
// =============================================

export type TwoFAStatusResponse = { two_factor_enabled: boolean };

export async function get2FAStatus(token: string) {
  return apiRequest<TwoFAStatusResponse>('/api/auth/2fa/status', { token });
}

export async function setup2FA(token: string) {
  return apiRequest<{ message: string }>('/api/auth/2fa/setup', {
    method: 'POST',
    token,
  });
}

export async function enable2FA(otp: string, token: string) {
  return apiRequest<{ message: string }>('/api/auth/2fa/enable', {
    method: 'POST',
    body: { otp },
    token,
  });
}

export async function disable2FA(password: string, token: string) {
  return apiRequest<{ message: string }>('/api/auth/2fa/disable', {
    method: 'POST',
    body: { password },
    token,
  });
}

export async function resend2FA(temp_token: string) {
  return apiRequest<{ message: string; temp_token: string }>('/api/auth/2fa/resend', {
    method: 'POST',
    body: { temp_token },
  });
}

export async function verify2FA(otp: string, temp_token: string) {
  return apiRequest<LoginSuccessResponse>('/api/auth/2fa/verify', {
    method: 'POST',
    body: { otp, temp_token },
  });
}
