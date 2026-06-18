import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Cross-Role Access & Full-Page Wrappers', () => {

  test('TI user can access process detail page (no 403)', async ({ page }) => {
    // TI users should be able to view process details without access errors
    await loginAs(page, 'ti');
    await page.goto('/procesos/1/');
    await expect(page.locator('h1, .card-header h6').first()).toBeVisible();
    await expect(page.locator('body')).not.toContainText('403');
    await expect(page.locator('body')).not.toContainText('Acceso Denegado');
  });

  test('Prevencion user can access process detail page (no 403)', async ({ page }) => {
    // Prevencion users should be able to view process details without access errors
    await loginAs(page, 'prevencion');
    await page.goto('/procesos/1/');
    await expect(page.locator('body')).not.toContainText('403');
    await expect(page.locator('body')).not.toContainText('Acceso Denegado');
  });

  test('Jefatura user is blocked from process detail page (403 expected)', async ({ page }) => {
    // Jefatura users should NOT have access to process detail pages
    await loginAs(page, 'jefatura');
    await page.goto('/procesos/1/');
    await expect(page.locator('body')).toContainText(/403|Acceso Denegado/);
  });

  test('Card detail full page shows sidebar, breadcrumbs, and content', async ({ page }) => {
    // Direct navigation to a task card detail page should render the full layout
    await loginAs(page, 'admin');
    await page.goto('/kanban/tarea/1/');
    await expect(page.locator('.sidebar')).toBeVisible();
    await expect(page.locator('.breadcrumb')).toBeVisible();
    await expect(page.locator('.card-header, .card-body').first()).toBeVisible();
  });

  test('Jefatura worker detail page shows full layout with sidebar', async ({ page }) => {
    // Jefatura users should see the full sidebar/breadcrumb layout on worker detail
    await loginAs(page, 'jefatura');
    await page.goto('/jefatura/');

    const workerLink = page.locator('a[href*="/jefatura/trabajador/"]').first();
    await expect(workerLink).toBeVisible({ timeout: 5000 });
    await workerLink.click();
    await expect(page.locator('.sidebar')).toBeVisible();
    await expect(page.locator('.breadcrumb')).toBeVisible();
  });

  test('Admin can access all 6 role dashboards without 403 errors', async ({ page }) => {
    // Admin users should be able to navigate to each role's dashboard
    await loginAs(page, 'admin');
    const dashboards = ['/rrhh/', '/ti/', '/jefatura/', '/prevencion/', '/finanzas/', '/logistica/'];
    for (const url of dashboards) {
      await page.goto(url);
      await expect(page.locator('body')).not.toContainText('403');
      await expect(page.locator('body')).not.toContainText('Acceso Denegado');
    }
  });

  test('Prevencion notifications page has breadcrumbs with Prevencion label', async ({ page }) => {
    // The prevencion notifications page should display breadcrumbs with "Prevencion" and "Notificaciones"
    await loginAs(page, 'prevencion');
    await page.goto('/prevencion/notificaciones/');
    await expect(page.locator('.breadcrumb')).toBeVisible();
    await expect(page.locator('.breadcrumb')).toContainText('Prevenci');
    await expect(page.locator('.breadcrumb')).toContainText('Notificaciones');
  });

  test('Jefatura notifications page has breadcrumbs with Jefatura label', async ({ page }) => {
    // The jefatura notifications page should display breadcrumbs with "Jefatura" and "Notificaciones"
    await loginAs(page, 'jefatura');
    await page.goto('/jefatura/notificaciones/');
    await expect(page.locator('.breadcrumb')).toBeVisible();
    await expect(page.locator('.breadcrumb')).toContainText('Jefatura');
    await expect(page.locator('.breadcrumb')).toContainText('Notificaciones');
  });

});
