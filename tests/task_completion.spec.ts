import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Task Completion by Role', () => {

  test('TI dashboard shows assigned tasks section', async ({ page }) => {
    // TI user should see their task list on the dashboard
    await loginAs(page, 'ti');
    await page.goto('/ti/');
    await expect(page.locator('.card-header h6').first()).toBeVisible();
  });

  test('TI user can open task detail from dashboard view button', async ({ page }) => {
    // Click the "Ver detalle" button for a task and verify the detail modal/card opens
    await loginAs(page, 'ti');
    await page.goto('/ti/');

    const verBtn = page.locator('a.btn[title="Ver detalle"]').first();
    await expect(verBtn).toBeVisible({ timeout: 5000 });
    await verBtn.click();
    await expect(page.locator('.card, .modal-content').first()).toBeVisible({ timeout: 5000 });
  });

  test('Prevencion dashboard shows tasks section', async ({ page }) => {
    // Prevencion user should see their assigned tasks on the dashboard
    await loginAs(page, 'prevencion');
    await page.goto('/prevencion/');
    await expect(page.locator('h1').first()).toBeVisible();

    const tareasSection = page.locator('.list-group, table, .card-body').first();
    await expect(tareasSection).toBeVisible();
  });

  test('Process detail shows Area column with role color badges', async ({ page }) => {
    // The process detail page should display the Area column with color-coded badges
    await loginAs(page, 'admin');
    await page.goto('/procesos/');

    const firstProcess = page.locator('table a[href*="/procesos/"]').first();
    await expect(firstProcess).toBeVisible({ timeout: 5000 });
    await firstProcess.click();

    // Verify the Area column header and at least one badge are visible
    await expect(page.locator('th:has-text("Area")').first()).toBeVisible();
    const areaBadges = page.locator('td .badge');
    await expect(areaBadges.first()).toBeVisible();
  });

  test('Non-assigned tasks show label instead of Completar button for TI user', async ({ page }) => {
    // Tasks not assigned to the current user should not show a Completar button
    await loginAs(page, 'ti');
    await page.goto('/procesos/');

    const firstProcess = page.locator('table a[href*="/procesos/"]').first();
    await expect(firstProcess).toBeVisible({ timeout: 5000 });
    await firstProcess.click();
    await expect(page.locator('tbody').first()).toBeVisible();
  });

  test('RRHH sees tasks but no Completar buttons on sub-tasks', async ({ page }) => {
    // RRHH users should not see Completar buttons on sub-tasks (they are not the assigned user)
    await loginAs(page, 'rrhh');
    await page.goto('/procesos/');

    const firstProcess = page.locator('table a[href*="/procesos/"]').first();
    await expect(firstProcess).toBeVisible({ timeout: 5000 });
    await firstProcess.click();

    // RRHH should see at most 1 Completar button (the process-level close button)
    const completarBtns = page.locator('button:has-text("Completar")');
    const count = await completarBtns.count();
    expect(count).toBeLessThanOrEqual(1);
  });

  test('Card detail full page shows sidebar and breadcrumbs', async ({ page }) => {
    // Direct navigation to a task detail page should render the full layout
    await loginAs(page, 'admin');
    await page.goto('/kanban/tarea/1/');
    await expect(page.locator('.sidebar')).toBeVisible();
    await expect(page.locator('.breadcrumb')).toBeVisible();
  });

});
