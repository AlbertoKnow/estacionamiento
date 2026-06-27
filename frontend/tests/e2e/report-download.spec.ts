import { test, expect } from '@playwright/test';

test.describe('Report download', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Código Institucional').fill('admin');
    await page.getByLabel('Contraseña').fill('admin123');
    await page.getByRole('button', { name: /ingresar/i }).click();
    await page.waitForURL(/\/dashboard/);
  });

  test('can navigate to reports page', async ({ page }) => {
    await page.getByRole('link', { name: /reportes/i }).click();
    await expect(page).toHaveURL(/\/reports/);
    await expect(page.getByText(/reporte de ocupación/i)).toBeVisible();
  });

  test('download users report triggers file download', async ({ page }) => {
    await page.goto('/reports');
    // Set a date range for occupancy report
    const dateFrom = page.locator('input[type="date"]').first();
    const dateTo = page.locator('input[type="date"]').nth(1);
    await dateFrom.fill('2026-01-01');
    await dateTo.fill('2026-12-31');

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.getByRole('button', { name: /descargar/i }).first().click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/reporte_ocupacion\.(xlsx|pdf)/);
  });
});
