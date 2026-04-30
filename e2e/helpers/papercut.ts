/**
 * Helpers for reading emails delivered to the Papercut SMTP test server.
 *
 * Papercut web API base: http://localhost:37408
 *
 * Endpoints:
 *   GET    /api/messages           → { totalMessageCount: N, messages: [{ id, createdAt, subject }] }
 *   GET    /api/messages/{id}      → { id, textBody, htmlBody, subject, from, to, ... }
 *   DELETE /api/messages           → deletes all messages (returns empty body)
 *
 * NOTE: message IDs contain spaces and must be URL-encoded when used in paths.
 */

import type { APIRequestContext } from '@playwright/test';

const PAPERCUT_BASE = process.env.PAPERCUT_BASE ?? 'http://localhost:37408';

/**
 * Delete all emails in Papercut so each test starts with a clean inbox.
 */
export async function clearEmails(request: APIRequestContext): Promise<void> {
  await request.delete(`${PAPERCUT_BASE}/api/messages`);
}

/**
 * Wait for an email to arrive and extract the first 6-digit OTP found in it.
 * Polls every second for up to `maxWaitMs` milliseconds.
 */
export async function getLatestOtp(
  request: APIRequestContext,
  maxWaitMs = 20_000
): Promise<string> {
  const deadline = Date.now() + maxWaitMs;

  while (Date.now() < deadline) {
    const listRes = await request.get(`${PAPERCUT_BASE}/api/messages`);
    if (listRes.ok()) {
      const listData = await listRes.json() as {
        totalMessageCount: number;
        messages: Array<{ id: string }>;
      };

      if (listData.totalMessageCount > 0 && listData.messages.length > 0) {
        const rawId = listData.messages[0].id;
        // URL-encode the ID (it contains spaces)
        const encodedId = encodeURIComponent(rawId);
        const msgRes = await request.get(`${PAPERCUT_BASE}/api/messages/${encodedId}`);
        if (msgRes.ok()) {
          const msg = await msgRes.json() as {
            textBody?: string;
            htmlBody?: string;
          };
          // Prefer plain-text body
          const body = msg.textBody ?? msg.htmlBody ?? '';
          const match = body.match(/\b(\d{6})\b/);
          if (match) return match[1];
        }
      }
    }

    await new Promise((r) => setTimeout(r, 1_000));
  }

  throw new Error(`No 6-digit OTP found in Papercut inbox after ${maxWaitMs}ms`);
}
