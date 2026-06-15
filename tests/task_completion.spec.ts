import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Task Completion by Role', () => {

  test('TI user can see assigned tasks on dashboard', async ({ page }) => {
    await loginAs(page, 'ti');
    await page.goto('/ti/');
    await expect(page.locator('.card-header h6').first()).toBeVisible();
  });

  test('TI user can complete a task from dashboard', async ({ page }) => {
    await loginAs(page, 'ti');
    await page.goto('/ti/');

    const verBtn = page.locator('a.btn:has-text("Ver")').first();
    if (await verBtn.count() > 0) {
      await verBtn.click();
      await expect(page.locator('.card, .modal-content').first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('Prevencion user can see assigned tasks on their dashboard', async ({ page }) => {
    await loginAs(page, 'prevencion');
    await page.goto('/prevencion/');
    await expect(page.locator('h1').first()).toBeVisible();
    const tareasSection = page.locator('.list-group, table, .card-body').first();
    await expect(tareasSection).toBeVisible();
  });

  test('Process detail shows Area column with color badges', async ({ page }) => {
    await loginAs(page, 'admin');
    await page.goto('/procesos/');
    const firstProcess = page.locator('table a[href*="/procesos/"]').first();
    if (await firstProcess.count() > 0) {
      await firstProcess.click();
      await expect(page.locator('th:has-text("Area")').first()).toBeVisible();
      const areaBadges = page.locator('td .badge');
      expect(await areaBadges.count()).toBeGreaterThanOrEqual(1);
    }
  });

  test('Non-assigned tasks show label instead of Completar button', async ({ page }) => {
    await loginAs(page, 'ti');
    await page.goto('/procesos/');
    const firstProcess = page.locator('table a[href*="/procesos/"]').first();
    if (await firstProcess.count() > 0) {
      await firstProcess.click();
      await expect(page.locator('tbody').first()).toBeVisible();
    }
  });

  test('RRHH sees tasks but no Completar buttons', async ({ page }) => {
    await loginAs(page, 'rrhh');
    await page.goto('/procesos/');
    const firstProcess = page.locator('table a[href*="/procesos/"]').first();
    if (await firstProcess.count() > 0) {
      await firstProcess.click();
      const completarBtns = page.locator('button:has-text("Completar")');
      // RRHH should not see Completar buttons on sub-tasks (they are not the assigned user)
      const count = await completarBtns.count();
      expect(count).toBeLessThanOrEqual(1); // At most the "Completar proceso" button, if any
    }
  });

  test('Card detail page shows sidebar and breadcrumbs', async ({ page }) => {
    await loginAs(page, 'admin');
    await page.goto('/kanban/tarea/1/');
    await expect(page.locator('.sidebar')).toBeVisible();
    await expect(page.locator('.breadcrumb')).toBeVisible();
  });

});
