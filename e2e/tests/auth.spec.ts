/**
 * E2E tests – Authentication flows
 *
 * NOTE: The backend ALWAYS requires OTP verification for every login.
 *       loginUser() handles this automatically via Papercut.
 *
 * Covers:
 *   1. End-user registration: 2-step form + OTP → dashboard
 *   2. Cleaner registration: 3-step form + OTP → dashboard
 *   3. Login with correct credentials + OTP → dashboard
 *   4. Login with wrong password → error alert (no OTP sent)
 *   5. Login with correct credentials + wrong OTP → error
 *   6. Login page shows Register link
 */

import { test, expect } from '@playwright/test';
import {
  registerEndUser,
  registerCleaner,
  loginUser,
  uniqueEmail,
} from '../helpers/auth';
import { clearEmails, getLatestOtp } from '../helpers/papercut';

const PASSWORD = 'Password1';

// ─── Registration ────────────────────────────────────────────────────────────

test.describe('Registration – end user', () => {
  test('completes 2-step form + OTP, lands on dashboard', async ({ page }) => {
    const email = uniqueEmail('eu');
    await registerEndUser(page, { email, password: PASSWORD });

    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByRole('button', { name: /logout/i })).toBeVisible();
  });

  test('shows error for weak password on step 1', async ({ page }) => {
    await page.goto('/register');
    await page.fill('input[type="email"]', uniqueEmail('pwtest'));
    await page.fill('input[type="password"]', 'short');
    // Disable HTML5 constraint validation so the app's handler runs
    await page.evaluate(() => {
      const form = document.querySelector('form');
      if (form) form.noValidate = true;
    });
    await page.click('button:has-text("Next: Your profile")');
    await expect(page.getByText(/password must be at least 8 characters/i)).toBeVisible();
  });

  test('shows error for invalid email on step 1', async ({ page }) => {
    await page.goto('/register');
    // Use an email without TLD — passes some HTML validators but fails the app regex
    await page.fill('input[type="email"]', 'notvalid');
    await page.fill('input[type="password"]', PASSWORD);
    // Disable HTML5 constraint validation so the app's onSubmit handler runs
    await page.evaluate(() => {
      const form = document.querySelector('form');
      if (form) form.noValidate = true;
    });
    await page.click('button:has-text("Next: Your profile")');
    await expect(page.getByText(/valid email/i)).toBeVisible();
  });
});

test.describe('Registration – cleaner', () => {
  test('completes 3-step cleaner form + OTP, lands on dashboard', async ({ page }) => {
    const email = uniqueEmail('cleaner-reg');
    await registerCleaner(page, { email, password: PASSWORD });
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByRole('button', { name: /logout/i })).toBeVisible();
  });
});

// ─── Login ───────────────────────────────────────────────────────────────────

test.describe('Login', () => {
  let userEmail: string;

  test.beforeAll(async ({ browser }) => {
    const ctx = await browser.newContext();
    const setupPage = await ctx.newPage();
    userEmail = uniqueEmail('login-user');
    await registerEndUser(setupPage, { email: userEmail, password: PASSWORD });
    await ctx.close();
  });

  test('correct credentials + OTP redirect to dashboard', async ({ page }) => {
    await loginUser(page, userEmail, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('wrong password shows error alert without OTP prompt', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', userEmail);
    await page.fill('input[type="password"]', 'WrongPass1');
    await page.click('button:has-text("Login")');
    // Backend rejects immediately with wrong password — no OTP form
    await expect(page.locator('.alert-danger')).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test('correct credentials + wrong OTP shows error', async ({ page }) => {
    await clearEmails(page.context().request);
    await page.goto('/login');
    await page.fill('input[type="email"]', userEmail);
    await page.fill('input[type="password"]', PASSWORD);
    await page.click('button:has-text("Login")');

    // OTP form appears
    await page.waitForSelector('input[placeholder="000000"]', { timeout: 15_000 });
    // Enter wrong OTP
    await page.fill('input[placeholder="000000"]', '000000');
    await page.click('button:has-text("Verify Code")');

    await expect(page.locator('.alert-danger')).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test('login page shows a Register link', async ({ page }) => {
    await page.goto('/login');
    // The Navbar and login form both render a Register link — use first()
    await expect(page.getByRole('link', { name: /register/i }).first()).toBeVisible();
  });
});

// ─── Resend OTP ───────────────────────────────────────────────────────────────

test.describe('Resend OTP during login', () => {
  let userEmail: string;

  test.beforeAll(async ({ browser }) => {
    const ctx = await browser.newContext();
    const setupPage = await ctx.newPage();
    userEmail = uniqueEmail('resend-user');
    await registerEndUser(setupPage, { email: userEmail, password: PASSWORD });
    await ctx.close();
  });

  test('resend code button sends a fresh OTP and login completes', async ({ page }) => {
    await clearEmails(page.context().request);
    await page.goto('/login');
    await page.fill('input[type="email"]', userEmail);
    await page.fill('input[type="password"]', PASSWORD);
    await page.click('button:has-text("Login")');

    await page.waitForSelector('input[placeholder="000000"]', { timeout: 15_000 });

    // Click resend to get a fresh OTP
    await clearEmails(page.context().request);
    await page.click('button:has-text("Resend code")');

    const otp = await getLatestOtp(page.context().request);
    await page.fill('input[placeholder="000000"]', otp);
    await page.click('button:has-text("Verify Code")');

    await expect(page).toHaveURL(/\/dashboard/);
  });
});
