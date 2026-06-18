import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Worker Management - Extended', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
  });

  test('Worker detail page shows all key information fields', async ({ page }) => {
    // The worker detail page should display RUN, nombre, cargo, and centro de costo
    await page.goto('/trabajadores/');
    const detailLink = page.locator('table a[title="Ficha"]').first();
    await expect(detailLink).toBeVisible({ timeout: 5000 });
    await detailLink.click();

    // Verify the detail h1 shows the worker's name
    await expect(page.locator('h1')).toBeVisible();
    // Verify key data fields are present in the detail list
    await expect(page.locator('dl')).toContainText('RUN');
    await expect(page.locator('dl')).toContainText('Nombre completo');
    await expect(page.locator('dl')).toContainText('Cargo');
  });

  test('Search and filter combo narrows worker list', async ({ page }) => {
    // Using both search and estado filter together should refine results
    await page.goto('/trabajadores/');
    await page.fill('input[name="q"]', 'Juan');
    await page.selectOption('select[name="estado"]', 'activo');
    await page.locator('button.btn-primary').click();

    // The filtered results should contain Juan in the table
    await expect(page.locator('table')).toContainText('Juan');
  });

  test('Create worker with duplicate RUN shows validation error', async ({ page }) => {
    // Submitting a worker with an existing RUN should show a validation error on the form
    await page.goto('/trabajadores/nuevo/');
    await expect(page.locator('.card-header h6')).toContainText('Nuevo Trabajador');

    // Use an existing RUN from seed data
    await page.fill('#id_run', '12.345.678-9');
    await page.fill('#id_nombre', 'Duplicate Worker');
    await page.fill('#id_correo', 'duplicate@test.cl');
    await page.fill('#id_cargo', 'Test');
    await page.selectOption('#id_centro_costo_actual', { index: 1 });
    await page.locator('button.btn-primary').click();

    // Should stay on the form page (not redirect) and show an error
    await expect(page).toHaveURL('/trabajadores/nuevo/');
    await expect(page.locator('.is-invalid, .text-danger, .alert')).toBeVisible();
  });

});
