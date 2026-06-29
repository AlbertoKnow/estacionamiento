import { test, expect } from '@playwright/test';

test.describe('Report download', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Código Institucional').fill('admin');
    await page.getByLabel('Contraseña').fill('admin123');
    await page.getByRole('button', { name: /ingresar/i }).click();
    await page.waitForURL(/\/dashboard/);
    await page.waitForLoadState('networkidle');
  });

  test('can navigate to reports page', async ({ page }) => {
    await page.getByRole('link', { name: /reportes/i }).click();
    await expect(page).toHaveURL(/\/reports/);
    await expect(page.getByText(/reporte de ocupación/i)).toBeVisible();
  });

  test('download button calls report API', async ({ page }) => {
    await page.goto('/reports');
    await page.waitForLoadState('networkidle');
    const dateFrom = page.locator('input[type="date"]').first();
    const dateTo = page.locator('input[type="date"]').nth(1);
    await dateFrom.fill('2026-01-01');
    await dateTo.fill('2026-12-31');

    const [request] = await Promise.all([
      page.waitForRequest((req) => req.url().includes('/reports/occupancy/')),
      page.getByRole('button', { name: /descargar/i }).first().click(),
    ]);
    expect(request.url()).toContain('/reports/occupancy/');
  });
});
