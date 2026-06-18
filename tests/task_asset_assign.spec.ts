import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Asset-Task Bridge (Asignar Activos)', () => {

  test('Asignar EPP page loads with available assets', async ({ page }) => {
    // Log in as prevencion and verify the "Asignar EPP" link exists (from seed data)
    await loginAs(page, 'prevencion');
    await page.goto('/prevencion/');

    const asignarBtn = page.locator('a:has-text("Asignar EPP")').first();
    await expect(asignarBtn).toBeVisible({ timeout: 5000 });
    await asignarBtn.click();
    await expect(page).toHaveURL(/\/asignar-activo\//);
    await expect(page.locator('.card-header h6').first()).toContainText(/Asignar|EPP/);

    // Verify at least one asset checkbox is available for assignment
    const assetCheckboxes = page.locator('input[name="activos"]');
    await expect(assetCheckboxes.first()).toBeVisible({ timeout: 5000 });
  });

  test('Asignar EPP page shows task context (worker, process, task info)', async ({ page }) => {
    await loginAs(page, 'prevencion');
    await page.goto('/prevencion/');

    const asignarBtn = page.locator('a:has-text("Asignar EPP")').first();
    await expect(asignarBtn).toBeVisible({ timeout: 5000 });
    await asignarBtn.click();
    await expect(page).toHaveURL(/\/asignar-activo\//);

    // Verify worker, process, and task context sections are visible on the page
    await expect(page.locator('.card-body').filter({ hasText: 'Trabajador' }).first()).toBeVisible();
    await expect(page.locator('.card-body').filter({ hasText: 'Proceso' }).first()).toBeVisible();
    await expect(page.locator('.card-body').filter({ hasText: 'Tarea' }).first()).toBeVisible();
  });

  test('Select assets and confirm — task completes', async ({ page }) => {
    await loginAs(page, 'prevencion');
    await page.goto('/prevencion/');

    const asignarBtn = page.locator('a:has-text("Asignar EPP")').first();
    await expect(asignarBtn).toBeVisible({ timeout: 5000 });
    await asignarBtn.click();
    await page.waitForURL(/\/asignar-activo\//);

    // Verify at least one asset is available before selecting
    const checkboxes = page.locator('input[name="activos"]');
    await expect(checkboxes.first()).toBeVisible({ timeout: 5000 });
    const count = await checkboxes.count();
    expect(count).toBeGreaterThanOrEqual(1);

    // Select the first two available assets
    await checkboxes.first().check();
    if (count > 1) await checkboxes.nth(1).check();

    // Submit the form and confirm the modal
    const confirmBtn = page.locator('button:has-text("Confirmar y completar")');
    await expect(confirmBtn).toBeVisible();
    await confirmBtn.click();
    await page.locator('#confirmModalBtn').click();

    // After completion, should redirect to process detail with success message
    await page.waitForURL(/\/procesos\/\d+\//);
    await expect(page.locator('.alert-success').first()).toBeVisible({ timeout: 5000 });
  });

  test('Completar sin asignar skips asset assignment', async ({ page }) => {
    await loginAs(page, 'prevencion');
    await page.goto('/prevencion/');

    const asignarBtn = page.locator('a:has-text("Asignar EPP")').first();
    await expect(asignarBtn).toBeVisible({ timeout: 5000 });
    await asignarBtn.click();
    await page.waitForURL(/\/asignar-activo\//);

    // Click the "Completar sin asignar" button to skip assignment
    const skipBtn = page.locator('button:has-text("Completar sin asignar")');
    await expect(skipBtn).toBeVisible({ timeout: 5000 });
    await skipBtn.click();
    await page.locator('#confirmModalBtn').click();

    // After completion, should redirect to process detail with a completion message
    await page.waitForURL(/\/procesos\/\d+\//);
    await expect(page.locator('.alert-success').first()).toContainText(/completada|sin asignar/);
  });

});
