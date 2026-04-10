/**
 * E2E tests – Job Request CRUD (end user perspective)
 *
 * Covers:
 *   1. Create a new job request – form fills and submits successfully
 *   2. Job request appears in the list after creation
 *   3. View job request detail via "View Details" link
 *   4. Edit a pending job request and save changes
 *   5. Delete a pending job request
 *   6. Cleaner is redirected away from the create form
 */

import { test, expect } from '@playwright/test';
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

  endUserEmail = uniqueEmail('jr-user');
  await registerEndUser(page, { email: endUserEmail, password: PASSWORD });

  cleanerEmail = uniqueEmail('jr-cleaner');
  await registerCleaner(page, { email: cleanerEmail, password: PASSWORD });

  await ctx.close();
});

// ─── Helper ───────────────────────────────────────────────────────────────────

function futureDateStr(daysAhead: number): string {
  const d = new Date();
  d.setDate(d.getDate() + daysAhead);
  return d.toISOString().split('T')[0];
}

// ─── Tests ───────────────────────────────────────────────────────────────────

test.describe('Job Request CRUD', () => {
  test('create a new job request and see it in the list', async ({ page }) => {
    await loginUser(page, endUserEmail, PASSWORD);
    await page.goto('/job-requests/new');
    await page.waitForSelector('h1:has-text("Create Job Request")');

    // Fill required fields
    await page.fill('input[placeholder="e.g., Weekly house cleaning"]', 'E2E Test Cleaning');
    // Switch to "Choose a cleaner" mode to avoid auto-assign interference
    await page.click('button:has-text("Choose a cleaner")');
    await page.selectOption('select.form-select >> nth=0', 'full');
    await page.fill('input[placeholder="e.g., 123 Main St, Singapore"]', '10 Orchard Road');
    await page.fill('input[type="date"]', futureDateStr(7));

    await page.click('button:has-text("Create job request")');
    await page.waitForURL('**/job-requests');

    await expect(page.getByText('E2E Test Cleaning')).toBeVisible();
  });

  test('view job request detail via View Details link', async ({ page }) => {
    await loginUser(page, endUserEmail, PASSWORD);
    await page.goto('/job-requests');
    await page.waitForSelector('text=E2E Test Cleaning');

    // Click View Details for the first matching job
    await page.locator('.card', { hasText: 'E2E Test Cleaning' }).getByRole('link', { name: 'View Details' }).first().click();

    await expect(page).toHaveURL(/\/job-requests\/\d+/);
    await expect(page.getByText('E2E Test Cleaning')).toBeVisible();
    // Pending jobs show Edit and Delete for end users
    await expect(page.getByRole('link', { name: /edit/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /delete/i })).toBeVisible();
  });

  test('edit a pending job request title and save changes', async ({ page }) => {
    await loginUser(page, endUserEmail, PASSWORD);
    await page.goto('/job-requests');
    await page.waitForSelector('text=E2E Test Cleaning');

    // Navigate to detail page
    await page.locator('.card', { hasText: 'E2E Test Cleaning' })
      .getByRole('link', { name: 'View Details' }).first().click();
    await page.waitForURL(/\/job-requests\/\d+/);

    // Click Edit
    await page.getByRole('link', { name: /edit/i }).click();
    await page.waitForURL(/\/job-requests\/\d+\/edit/);

    // Update the title
    const titleInput = page.locator('input[type="text"]').first();
    await titleInput.clear();
    await titleInput.fill('Updated E2E Cleaning');

    await page.click('button:has-text("Save Changes")');
    await page.waitForURL(/\/job-requests/);

    await expect(page.getByText('Updated E2E Cleaning')).toBeVisible();
  });

  test('delete a pending job request', async ({ page }) => {
    // Create a dedicated job so we don't affect other tests
    await loginUser(page, endUserEmail, PASSWORD);
    await page.goto('/job-requests/new');

    await page.fill('input[placeholder="e.g., Weekly house cleaning"]', 'To Be Deleted');
    await page.click('button:has-text("Choose a cleaner")');
    await page.selectOption('select.form-select >> nth=0', 'partial');
    await page.fill('input[placeholder="e.g., 123 Main St, Singapore"]', '5 Delete Ave');
    await page.fill('input[type="date"]', futureDateStr(3));
    await page.click('button:has-text("Create job request")');
    await page.waitForURL('**/job-requests');

    // Open the job
    await page.locator('.card', { hasText: 'To Be Deleted' })
      .getByRole('link', { name: 'View Details' }).first().click();
    await page.waitForURL(/\/job-requests\/\d+/);

    // Confirm and delete
    page.once('dialog', (dialog) => dialog.accept());
    await page.click('button:has-text("Delete")');

    // Redirected back to list; job should not appear
    await page.waitForURL(/\/job-requests$/);
    await expect(page.getByText('To Be Deleted')).not.toBeVisible();
  });

  test('cleaner is redirected away from the create page', async ({ page }) => {
    await loginUser(page, cleanerEmail, PASSWORD);
    await page.goto('/job-requests/new');
    // Cleaner is not end_user → redirected to /job-requests
    await page.waitForURL(/\/job-requests$/);
  });
});
