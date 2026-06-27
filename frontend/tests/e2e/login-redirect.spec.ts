import { test, expect } from '@playwright/test';

// Uses the superuser created during backend setup: admin / admin123
// Role: RECTOR — should redirect to /dashboard

test.describe('Login redirect by role', () => {
  test('RECTOR login redirects to /dashboard', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Código Institucional').fill('admin');
    await page.getByLabel('Contraseña').fill('admin123');
    await page.getByRole('button', { name: /ingresar/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 5000 });
  });

  test('invalid credentials show error', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Código Institucional').fill('noexiste');
    await page.getByLabel('Contraseña').fill('wrongpass');
    await page.getByRole('button', { name: /ingresar/i }).click();
    await expect(page.getByText(/credenciales|error/i)).toBeVisible({ timeout: 5000 });
  });

  test('empty form shows validation error', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('button', { name: /ingresar/i }).click();
    await expect(page.getByText(/campo requerido/i)).toBeVisible();
  });

  test('unauthenticated access to /dashboard redirects to /login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
  });
});
