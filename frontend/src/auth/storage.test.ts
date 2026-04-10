/**
 * Utility function tests — src/auth/storage.ts
 *
 * Tests cover: getToken, getUser, setAuth, clearAuth
 * using jsdom's localStorage (no mocking required).
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { getToken, getUser, setAuth, clearAuth } from './storage';

const MOCK_USER = {
  id: 1,
  email: 'test@example.com',
  role: 'end_user' as const,
  created_at: '2024-01-01T00:00:00Z',
};

describe('auth/storage utilities', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('getToken returns null when nothing is stored', () => {
    expect(getToken()).toBeNull();
  });

  it('setAuth persists token so getToken returns it', () => {
    setAuth('my-jwt-token', MOCK_USER);
    expect(getToken()).toBe('my-jwt-token');
  });

  it('getUser returns the stored user after setAuth', () => {
    setAuth('my-jwt-token', MOCK_USER);
    expect(getUser()).toEqual(MOCK_USER);
  });

  it('clearAuth removes both token and user', () => {
    setAuth('my-jwt-token', MOCK_USER);
    clearAuth();
    expect(getToken()).toBeNull();
    expect(getUser()).toBeNull();
  });

  it('getUser returns null when the stored value is corrupt JSON', () => {
    localStorage.setItem('cm_user', '{not valid json{{');
    expect(getUser()).toBeNull();
  });
});
