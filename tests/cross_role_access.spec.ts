import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Cross-Role Access & Full-Page Wrappers', () => {

  test('TI can access process detail page', async ({ page }) => {
    await loginAs(page, 'ti');
    await page.goto('/procesos/1/');
    await expect(page.locator('h1, .card-header h6').first()).toBeVisible();
    await expect(page.locator('body')).not.toContainText('403');
    await expect(page.locator('body')).not.toContainText('Acceso Denegado');
  });

  test('Prevencion can access process detail page', async ({ page }) => {
    await loginAs(page, 'prevencion');
    await page.goto('/procesos/1/');
    await expect(page.locator('body')).not.toContainText('403');
    await expect(page.locator('body')).not.toContainText('Acceso Denegado');
  });

  test('Jefatura cannot access process detail page', async ({ page }) => {
    await loginAs(page, 'jefatura');
    await page.goto('/procesos/1/');
    await expect(page.locator('body')).toContainText(/403|Acceso Denegado/);
  });

  test('Card detail page shows sidebar', async ({ page }) => {
    await loginAs(page, 'admin');
    await page.goto('/kanban/tarea/1/');
    await expect(page.locator('.sidebar')).toBeVisible();
    await expect(page.locator('.breadcrumb')).toBeVisible();
    await expect(page.locator('.card-header, .card-body').first()).toBeVisible();
  });

  test('Jefatura worker detail shows full layout', async ({ page }) => {
    await loginAs(page, 'jefatura');
    await page.goto('/jefatura/');
    const workerLink = page.locator('a[href*="/jefatura/trabajador/"]').first();
    if (await workerLink.count() > 0) {
      await workerLink.click();
      await expect(page.locator('.sidebar')).toBeVisible();
      await expect(page.locator('.breadcrumb')).toBeVisible();
    }
  });

  test('Admin can access all role dashboards', async ({ page }) => {
    await loginAs(page, 'admin');
    const urls = ['/rrhh/', '/ti/', '/jefatura/', '/prevencion/', '/finanzas/', '/logistica/'];
    for (const url of urls) {
      await page.goto(url);
      await expect(page.locator('body')).not.toContainText('403');
      await expect(page.locator('body')).not.toContainText('Acceso Denegado');
    }
  });

  test('Prevencion notification page has breadcrumbs', async ({ page }) => {
    await loginAs(page, 'prevencion');
    await page.goto('/prevencion/notificaciones/');
    await expect(page.locator('.breadcrumb')).toBeVisible();
    await expect(page.locator('.breadcrumb')).toContainText('Prevenci');
    await expect(page.locator('.breadcrumb')).toContainText('Notificaciones');
  });

  test('Jefatura notification page has breadcrumbs', async ({ page }) => {
    await loginAs(page, 'jefatura');
    await page.goto('/jefatura/notificaciones/');
    await expect(page.locator('.breadcrumb')).toBeVisible();
    await expect(page.locator('.breadcrumb')).toContainText('Jefatura');
    await expect(page.locator('.breadcrumb')).toContainText('Notificaciones');
  });

});
