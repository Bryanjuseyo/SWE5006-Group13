import { apiRequest } from './client';

export type UserRole = 'end_user' | 'cleaner' | 'administrator';

export type RegisterRequest = {
  email: string;
  password: string;
  role: UserRole;
};

export type RegisterResponse = {
  message: string;
  user: { id: number; email: string; role: UserRole; created_at: string };
};

export async function register(req: RegisterRequest) {
  return apiRequest<RegisterResponse>('/api/auth/register', {
    method: 'POST',
    body: req,
  });
}

export type LoginRequest = { email: string; password: string };

export type LoginResponse = {
  message: string;
  token: string;
  user: { id: number; email: string; role: UserRole; created_at: string };
};

export async function login(req: LoginRequest) {
  return apiRequest<LoginResponse>('/api/auth/login', {
    method: 'POST',
    body: req,
  });
}
