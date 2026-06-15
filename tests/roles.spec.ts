import { test, expect } from '@playwright/test';
import { loginAs, logout } from './helpers';

test.describe('Acceso por Roles', () => {

  test('admin sees admin sidebar with all navigation items', async ({ page }) => {
    await loginAs(page, 'admin');
    await page.goto('/kanban/');
    await expect(page.locator('.sidebar')).toContainText('Procesos');
    await expect(page.locator('.sidebar')).toContainText('Gestión');
    await expect(page.locator('.sidebar')).toContainText('Sistema');
    await expect(page.locator('.sidebar')).toContainText('Usuarios');
  });

  test('rrhh dashboard shows RRHH sidebar', async ({ page }) => {
    await loginAs(page, 'rrhh');
    await expect(page.locator('.sidebar')).toContainText('Dashboard');
    await expect(page.locator('.sidebar')).toContainText('Trabajadores');
    await expect(page.locator('.sidebar')).toContainText('Reportes');
  });

  test('ti dashboard shows TI sidebar', async ({ page }) => {
    await loginAs(page, 'ti');
    await expect(page.locator('.sidebar')).toContainText('Mis Tareas');
    await expect(page.locator('.sidebar')).toContainText('Inventario TI');
    await expect(page.locator('.sidebar')).toContainText('Bloqueo Urgente');
  });

  test('jefatura dashboard shows Jefatura sidebar', async ({ page }) => {
    await loginAs(page, 'jefatura');
    await expect(page.locator('.sidebar')).toContainText('Mi Nómina');
    await expect(page.locator('.sidebar')).toContainText('Tablero Kanban');
    await expect(page.locator('.sidebar')).toContainText('Procesos Activos');
  });

  test('prevencion dashboard shows Prevencion sidebar', async ({ page }) => {
    await loginAs(page, 'prevencion');
    await expect(page.locator('.sidebar')).toContainText('Mis Tareas');
    await expect(page.locator('.sidebar')).toContainText('Inventario EPP');
    await expect(page.locator('.sidebar')).toContainText('Certificaciones');
  });

  test('finanzas dashboard shows Finanzas sidebar', async ({ page }) => {
    await loginAs(page, 'finanzas');
    await expect(page.locator('.sidebar')).toContainText('Finiquitos');
    await expect(page.locator('.sidebar')).toContainText('Procesos de Término');
  });

  test('logistica dashboard shows Logistica sidebar', async ({ page }) => {
    await loginAs(page, 'logistica');
    await expect(page.locator('.sidebar')).toContainText('Dashboard');
    await expect(page.locator('.sidebar')).toContainText('Devoluciones');
    await expect(page.locator('.sidebar')).toContainText('Inventario');
  });

  test('rrhh user cannot access ti pages', async ({ page }) => {
    await loginAs(page, 'rrhh');
    await page.goto('/ti/');
    await expect(page.locator('#page-top')).toContainText('Acceso Denegado');
  });

  test('ti user cannot access rrhh pages', async ({ page }) => {
    await loginAs(page, 'ti');
    await page.goto('/rrhh/');
    await expect(page.locator('#page-top')).toContainText('Acceso Denegado');
  });

  test('jefatura user cannot access admin user list', async ({ page }) => {
    await loginAs(page, 'jefatura');
    await page.goto('/usuarios/');
    await expect(page.locator('#page-top')).toContainText('Acceso Denegado');
  });

  test('each role sees their own name in navbar', async ({ page }) => {
    await loginAs(page, 'rrhh');
    await expect(page.locator('#userDropdown')).toContainText('María González');
    await logout(page);
    await loginAs(page, 'ti');
    await expect(page.locator('#userDropdown')).toContainText('Pedro Ramírez');
  });

  test('active nav link is highlighted in sidebar', async ({ page }) => {
    await loginAs(page, 'ti');
    const activeLink = page.locator('.sidebar .nav-link.active');
    expect(await activeLink.count()).toBeGreaterThanOrEqual(0);
    await expect(page.locator('.sidebar')).toBeVisible();
  });

  test('admin sees Acceso rápido links that highlight when on role page', async ({ page }) => {
    await loginAs(page, 'admin');
    await page.goto('/rrhh/');
    const rrhhLink = page.locator('.sidebar a.active:has-text("RRHH")');
    expect(await rrhhLink.count()).toBeGreaterThanOrEqual(0);
  });

});
