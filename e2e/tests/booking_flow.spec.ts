/**
 * E2E tests – Full booking completion flow
 *
 * Happy-path scenario:
 *   1. End user creates a job request (pending, no cleaner assigned)
 *   2. Cleaner visits /cleaner/browse-jobs and accepts the job (→ confirmed)
 *      – BrowseJobsPage has an "Accept Job" button per card and navigates to
 *        /cleaner/schedule after accepting.
 *   3. On /cleaner/schedule: cleaner clicks "Start Job" (→ in_progress, no confirm dialog)
 *   4. On /cleaner/schedule: cleaner clicks "Mark Complete" (→ cleaner_completed)
 *   5. End user navigates to the job detail page and clicks "Confirm Completion"
 *      (→ completed, requires confirm dialog)
 *
 * Additional scenarios:
 *   6. Cleaner declines a pending job (→ cancelled)
 *   7. End user cancels after cleaner accepted (→ cancelled)
 */

import { test, expect, type Page } from '@playwright/test';
import {
  registerEndUser,
  registerCleaner,
  loginUser,
  uniqueEmail,
} from '../helpers/auth';

const PASSWORD = 'Password1';

let endUserEmail: string;
let cleanerEmail: string;

test.beforeAll(async ({ browser }) => {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();

  endUserEmail = uniqueEmail('bf-user');
  await registerEndUser(page, { email: endUserEmail, password: PASSWORD });

  cleanerEmail = uniqueEmail('bf-cleaner');
  await registerCleaner(page, {
    email: cleanerEmail,
    password: PASSWORD,
    serviceType: 'full',
    hourlyRate: '30',
    yearsExperience: '3',
  });

  await ctx.close();
});

// ─── Helper: create a job request as end user, returns the job ID ─────────────

async function createJob(page: Page, title: string): Promise<number> {
  await page.goto('/job-requests/new');
  await page.waitForSelector('input[placeholder="e.g., Weekly house cleaning"]');

  await page.fill('input[placeholder="e.g., Weekly house cleaning"]', title);
  // "Choose a cleaner" mode → no auto-assign
  await page.click('button:has-text("Choose a cleaner")');
  await page.selectOption('select.form-select >> nth=0', 'full');
  await page.fill('input[placeholder="e.g., 123 Main St, Singapore"]', '88 Booking Ave');

  const future = new Date();
  future.setDate(future.getDate() + 5);
  await page.fill('input[type="date"]', future.toISOString().split('T')[0]);

  await page.click('button:has-text("Create job request")');
  await page.waitForURL('**/job-requests');

  // Navigate to detail to capture the job ID
  await page.locator('.card', { hasText: title })
    .getByRole('link', { name: 'View Details' }).click();
  await page.waitForURL(/\/job-requests\/\d+/);
  const url = page.url();
  const idMatch = url.match(/\/job-requests\/(\d+)/);
  if (!idMatch) throw new Error(`Could not extract job ID from URL: ${url}`);

  // Go back to list
  await page.goto('/job-requests');
  return parseInt(idMatch[1], 10);
}

// ─── Happy path ───────────────────────────────────────────────────────────────

test.describe('Full booking completion flow', () => {
  test('pending → confirmed → in_progress → cleaner_completed → completed', async ({
    browser,
  }) => {
    const euCtx = await browser.newContext();
    const clCtx = await browser.newContext();
    const euPage = await euCtx.newPage();
    const clPage = await clCtx.newPage();

    try {
      // ── 1. End user creates the job ───────────────────────────────────────
      await loginUser(euPage, endUserEmail, PASSWORD);
      const title = `Full Flow ${Date.now()}`;
      const jobId = await createJob(euPage, title);

      // ── 2. Cleaner accepts the job from BrowseJobsPage ────────────────────
      await loginUser(clPage, cleanerEmail, PASSWORD);
      await clPage.goto('/cleaner/browse-jobs');
      await clPage.waitForSelector(`text=${title}`, { timeout: 15_000 });
      await clPage.locator('.card', { hasText: title })
        .getByRole('button', { name: 'Accept Job' }).click();
      // After accepting, navigates to /cleaner/schedule
      await clPage.waitForURL('**/cleaner/schedule');
      await expect(clPage.getByText(title)).toBeVisible();

      // ── 3. Cleaner starts the job (no confirm dialog needed) ──────────────
      await clPage.locator('.card', { hasText: title })
        .getByRole('button', { name: 'Start Job' }).click();
      await expect(
        clPage.locator('.card', { hasText: title }).locator('.badge', { hasText: /in.progress/i })
      ).toBeVisible();

      // ── 4. Cleaner marks the job as complete ──────────────────────────────
      await clPage.locator('.card', { hasText: title })
        .getByRole('button', { name: 'Mark Complete' }).click();
      // Schedule only shows confirmed / in_progress → card disappears
      await expect(clPage.locator('.card', { hasText: title })).not.toBeVisible();

      // ── 5. End user confirms completion ───────────────────────────────────
      await euPage.goto(`/job-requests/${jobId}`);
      // Wait for the detail page to fully render (card-header)
      await euPage.waitForSelector('.card-header', { timeout: 10_000 });
      // Use span.badge to avoid matching the status <select> option
      await expect(
        euPage.locator('span.badge', { hasText: /awaiting your confirmation/i })
      ).toBeVisible();

      euPage.once('dialog', (d) => d.accept());
      await euPage.click('button:has-text("Confirm Completion")');

      await expect(
        euPage.locator('span.badge', { hasText: /completed/i })
      ).toBeVisible();
    } finally {
      await euCtx.close();
      await clCtx.close();
    }
  });
});

// ─── Cleaner cancels an accepted job ─────────────────────────────────────────
//
// The backend only allows a cleaner to "decline" if they are the preferred
// cleaner on a pending job. The cleaner CAN cancel a job they have already
// confirmed (accepted). This test verifies that flow.

test.describe('Cleaner cancels an accepted job', () => {
  test('cleaner cancels confirmed job from schedule page → status becomes cancelled', async ({
    browser,
  }) => {
    const euCtx = await browser.newContext();
    const clCtx = await browser.newContext();
    const euPage = await euCtx.newPage();
    const clPage = await clCtx.newPage();

    try {
      // End user creates the job
      await loginUser(euPage, endUserEmail, PASSWORD);
      const title = `Cleaner Cancel Test ${Date.now()}`;
      const jobId = await createJob(euPage, title);

      // Cleaner accepts the job (→ confirmed, cleaner_id is now set)
      await loginUser(clPage, cleanerEmail, PASSWORD);
      await clPage.goto('/cleaner/browse-jobs');
      await clPage.waitForSelector(`text=${title}`, { timeout: 15_000 });
      await clPage.locator('.card', { hasText: title })
        .getByRole('button', { name: 'Accept Job' }).click();
      await clPage.waitForURL('**/cleaner/schedule');

      // Cleaner cancels from the schedule page ("Cancel Job" with confirm dialog)
      clPage.once('dialog', (d) => d.accept());
      await clPage.locator('.card', { hasText: title })
        .getByRole('button', { name: 'Cancel Job' }).click();
      // Card disappears from schedule (schedule only shows confirmed / in_progress)
      await expect(clPage.locator('.card', { hasText: title })).not.toBeVisible();

      // End user verifies the status is now Cancelled
      await euPage.goto(`/job-requests/${jobId}`);
      await euPage.waitForSelector('.card-header', { timeout: 10_000 });
      await expect(
        euPage.locator('span.badge', { hasText: /cancelled/i })
      ).toBeVisible();
    } finally {
      await euCtx.close();
      await clCtx.close();
    }
  });
});

// ─── End user cancels after acceptance ───────────────────────────────────────

test.describe('End user cancels a confirmed job', () => {
  test('cancel after cleaner accepted → status becomes cancelled', async ({ browser }) => {
    const euCtx = await browser.newContext();
    const clCtx = await browser.newContext();
    const euPage = await euCtx.newPage();
    const clPage = await clCtx.newPage();

    try {
      // End user creates job, capture ID
      await loginUser(euPage, endUserEmail, PASSWORD);
      const title = `Cancel Test ${Date.now()}`;
      const jobId = await createJob(euPage, title);

      // Cleaner accepts from BrowseJobsPage
      await loginUser(clPage, cleanerEmail, PASSWORD);
      await clPage.goto('/cleaner/browse-jobs');
      await clPage.waitForSelector(`text=${title}`, { timeout: 15_000 });
      await clPage.locator('.card', { hasText: title })
        .getByRole('button', { name: 'Accept Job' }).click();
      await clPage.waitForURL('**/cleaner/schedule');

      // End user cancels from the detail page
      await euPage.goto(`/job-requests/${jobId}`);
      await euPage.waitForSelector('.card-header', { timeout: 10_000 });

      euPage.once('dialog', (d) => d.accept());
      await euPage.click('button:has-text("Cancel Request")');

      await expect(
        euPage.locator('span.badge', { hasText: /cancelled/i })
      ).toBeVisible();
    } finally {
      await euCtx.close();
      await clCtx.close();
    }
  });
});
