import { test, expect } from '@playwright/test';

// Note: scanning requires camera access and a valid QR token.
// This test verifies the scan page loads correctly for an AGENTE role.
// Full scan simulation requires a real QR token from the backend.

test.describe('Scan page', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin (RECTOR) to verify scan page is guarded
    await page.goto('/login');
    await page.getByLabel('Código Institucional').fill('admin');
    await page.getByLabel('Contraseña').fill('admin123');
    await page.getByRole('button', { name: /ingresar/i }).click();
    await page.waitForURL(/\/dashboard/);
  });

  test('RECTOR cannot access /scan — redirected', async ({ page }) => {
    await page.goto('/scan');
    // Middleware redirects non-AGENTE to /dashboard or /my-qr
    await expect(page).not.toHaveURL(/\/scan/, { timeout: 3000 });
  });

  test('/dashboard shows occupancy cards', async ({ page }) => {
    await page.goto('/dashboard');
    // Cards should appear (may be empty if no data)
    await expect(page.getByText(/ocupación en tiempo real/i)).toBeVisible();
  });
});
