/**
 * Reusable auth helpers for Playwright E2E tests.
 *
 * IMPORTANT: The backend always requires OTP verification for every login —
 * even if the user has not opted into 2FA. loginUser handles this automatically.
 *
 * registerEndUser  – 2-step registration form + email OTP (ends on /dashboard)
 * registerCleaner  – 3-step registration form + email OTP (ends on /dashboard)
 * loginUser        – fills email/password, reads OTP from Papercut, completes login
 * uniqueEmail      – timestamp-based unique email to avoid inter-test conflicts
 */

import type { Page } from '@playwright/test';
import { clearEmails, getLatestOtp } from './papercut';

export interface EndUserOptions {
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
}

export interface CleanerOptions extends EndUserOptions {
  serviceType?: 'partial' | 'full';
  hourlyRate?: string;
  yearsExperience?: string;
}

/**
 * Register a new end_user account through the UI, including OTP verification.
 * After this resolves the user is logged in and on /dashboard.
 */
export async function registerEndUser(page: Page, opts: EndUserOptions): Promise<void> {
  const { email, password, firstName = 'Test', lastName = 'User' } = opts;

  await clearEmails(page.context().request);
  await page.goto('/register');

  // ── Step 1: account info ──────────────────────────────────────────────────
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  // Role select defaults to "end_user" — no change needed
  await page.click('button:has-text("Next: Your profile")');

  // ── Step 2: personal info ─────────────────────────────────────────────────
  await page.waitForSelector('input[placeholder="Jane"]');
  await page.fill('input[placeholder="Jane"]', firstName);
  await page.fill('input[placeholder="Doe"]', lastName);
  await page.click('button:has-text("Complete registration")');

  // ── OTP verification (email verification) ─────────────────────────────────
  await page.waitForSelector('input[placeholder="000000"]');
  const otp = await getLatestOtp(page.context().request);
  await page.fill('input[placeholder="000000"]', otp);
  await page.click('button:has-text("Complete registration")');

  await page.waitForURL('**/dashboard**');
}

/**
 * Register a new cleaner account (3 steps) + OTP verification.
 */
export async function registerCleaner(page: Page, opts: CleanerOptions): Promise<void> {
  const {
    email,
    password,
    firstName = 'Clean',
    lastName = 'Pro',
    serviceType = 'full',
    hourlyRate = '25',
    yearsExperience = '2',
  } = opts;

  await clearEmails(page.context().request);
  await page.goto('/register');

  // ── Step 1 ────────────────────────────────────────────────────────────────
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.selectOption('select', 'cleaner');
  await page.click('button:has-text("Next: Your profile")');

  // ── Step 2 ────────────────────────────────────────────────────────────────
  await page.waitForSelector('input[placeholder="Jane"]');
  await page.fill('input[placeholder="Jane"]', firstName);
  await page.fill('input[placeholder="Doe"]', lastName);
  await page.click('button:has-text("Next: Cleaner details")');

  // ── Step 3 ────────────────────────────────────────────────────────────────
  await page.waitForSelector('input[placeholder="e.g. 25.50"]');
  await page.selectOption('select', serviceType);
  await page.fill('input[placeholder="e.g. 25.50"]', hourlyRate);
  await page.fill('input[placeholder="e.g. 2"]', yearsExperience);
  await page.click('button:has-text("Complete registration")');

  // ── OTP verification ──────────────────────────────────────────────────────
  await page.waitForSelector('input[placeholder="000000"]');
  const otp = await getLatestOtp(page.context().request);
  await page.fill('input[placeholder="000000"]', otp);
  await page.click('button:has-text("Complete registration")');

  await page.waitForURL('**/dashboard**');
}

/**
 * Log in an existing user.
 * The backend ALWAYS sends an OTP for every login — this function reads
 * the OTP from Papercut automatically and completes verification.
 * After resolving the browser is on /dashboard.
 */
export async function loginUser(page: Page, email: string, password: string): Promise<void> {
  // Clear inbox so the OTP we read belongs to this login attempt
  await clearEmails(page.context().request);

  await page.goto('/login');
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button:has-text("Login")');

  // Backend always returns requires_2fa:true and shows the OTP form
  await page.waitForSelector('input[placeholder="000000"]', { timeout: 15_000 });
  const otp = await getLatestOtp(page.context().request);
  await page.fill('input[placeholder="000000"]', otp);
  await page.click('button:has-text("Verify Code")');

  await page.waitForURL('**/dashboard**');
}

/** Generate a unique email to avoid inter-test conflicts. */
export function uniqueEmail(prefix: string): string {
  return `${prefix}.${Date.now()}@test.local`;
}
