import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Asset-Task Bridge (Asignar Activos)', () => {

  test('Asignar EPP page loads with available assets', async ({ page }) => {
    await loginAs(page, 'prevencion');
    await page.goto('/prevencion/');

    const asignarBtn = page.locator('a:has-text("Asignar EPP")').first();
    if (await asignarBtn.count() > 0) {
      await asignarBtn.click();
      await expect(page).toHaveURL(/\/asignar-activo\//);
      await expect(page.locator('.card-header h6').first()).toContainText(/Asignar|EPP/);
      const assetCheckboxes = page.locator('input[name="activos"]');
      expect(await assetCheckboxes.count()).toBeGreaterThanOrEqual(1);
    }
  });

  test('Asignar EPP page shows task context', async ({ page }) => {
    await loginAs(page, 'prevencion');
    await page.goto('/prevencion/');
    const asignarBtn = page.locator('a:has-text("Asignar EPP")').first();
    if (await asignarBtn.count() > 0) {
      await asignarBtn.click();
      await expect(page.locator('.card-body').filter({ hasText: 'Trabajador' }).first()).toBeVisible();
      await expect(page.locator('.card-body').filter({ hasText: 'Proceso' }).first()).toBeVisible();
      await expect(page.locator('.card-body').filter({ hasText: 'Tarea' }).first()).toBeVisible();
    }
  });

  test('Select assets and confirm — task completes', async ({ page }) => {
    await loginAs(page, 'prevencion');
    await page.goto('/prevencion/');
    const asignarBtn = page.locator('a:has-text("Asignar EPP")').first();
    if (await asignarBtn.count() > 0) {
      await asignarBtn.click();
      await page.waitForURL(/\/asignar-activo\//);
      const checkboxes = page.locator('input[name="activos"]');
      const count = await checkboxes.count();
      if (count > 0) {
        await checkboxes.first().check();
        if (count > 1) await checkboxes.nth(1).check();
        const confirmBtn = page.locator('button:has-text("Confirmar y completar")');
        await confirmBtn.click();
        await page.locator('#confirmModalBtn').click();
        await page.waitForURL(/\/procesos\/\d+\//);
        await expect(page.locator('.alert-success').first()).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('Completar sin asignar skips asset assignment', async ({ page }) => {
    await loginAs(page, 'prevencion');
    await page.goto('/prevencion/');
    const asignarBtn = page.locator('a:has-text("Asignar EPP")').first();
    if (await asignarBtn.count() > 0) {
      await asignarBtn.click();
      await page.waitForURL(/\/asignar-activo\//);
      const skipBtn = page.locator('button:has-text("Completar sin asignar")');
      if (await skipBtn.count() > 0) {
        await skipBtn.click();
        await page.locator('#confirmModalBtn').click();
        await page.waitForURL(/\/procesos\/\d+\//);
        await expect(page.locator('.alert-success').first()).toContainText(/completada|sin asignar/);
      }
    }
  });

});
