import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Task Detail Access by Role', () => {

  test('Admin can view task detail page with full layout', async ({ page }) => {
    // Admin should always have access to card detail pages
    await loginAs(page, 'admin');
    await page.goto('/kanban/tarea/1/');
    await expect(page.locator('.sidebar')).toBeVisible();
    await expect(page.locator('.breadcrumb')).toBeVisible();
    await expect(page.locator('.card')).toContainText('Detalle de Tarea');
  });

  test('Prevencion can view task detail page (no 403 error)', async ({ page }) => {
    // Prevencion role should now have access to card_detail (fixed roles_requeridos bug)
    await loginAs(page, 'prevencion');
    await page.goto('/kanban/tarea/1/');
    // Verify there's no access denied error
    await expect(page.locator('body')).not.toContainText('403');
    await expect(page.locator('body')).not.toContainText('Acceso Denegado');
    // Verify the page renders with the task detail header
    await expect(page.locator('.breadcrumb')).toBeVisible();
  });

  test('TI user can view task detail page with breadcrumbs', async ({ page }) => {
    // TI role should have access to card_detail and see the full layout
    await loginAs(page, 'ti');
    await page.goto('/kanban/tarea/1/');
    await expect(page.locator('.breadcrumb')).toBeVisible();
    await expect(page.locator('.card')).toContainText('Detalle de Tarea');
  });

  test('Finanzas user can view task detail page with breadcrumbs', async ({ page }) => {
    // Finanzas role should have access to card_detail
    await loginAs(page, 'finanzas');
    await page.goto('/kanban/tarea/1/');
    await expect(page.locator('.breadcrumb')).toBeVisible();
    await expect(page.locator('.card')).toContainText('Detalle de Tarea');
  });

  test('Logistica user can view task detail page with breadcrumbs', async ({ page }) => {
    // Logistica role should have access to card_detail
    await loginAs(page, 'logistica');
    await page.goto('/kanban/tarea/1/');
    await expect(page.locator('.breadcrumb')).toBeVisible();
    await expect(page.locator('.card')).toContainText('Detalle de Tarea');
  });

  test('Jefatura user is blocked from task detail page', async ({ page }) => {
    // Jefatura should NOT have access to generic kanban card detail (not in roles_requeridos)
    await loginAs(page, 'jefatura');
    await page.goto('/kanban/tarea/1/');
    await expect(page.locator('body')).toContainText(/403|Acceso Denegado/);
  });

});
