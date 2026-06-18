import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Clientes', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
  });

  test('client list shows seeded clients', async ({ page }) => {
    await page.goto('/clientes/');
    await expect(page.locator('h1')).toContainText('Clientes');
    await expect(page.locator('table')).toContainText('Codelco');
    await expect(page.locator('table')).toContainText('BHP');
    await expect(page.locator('table')).toContainText('Minera Los Pelambres');
    await expect(page.locator('table')).toContainText('Anglo American');
  });

  test('create new client', async ({ page }) => {
    await page.goto('/clientes/nuevo/');
    await expect(page.locator('.card-header h6')).toContainText('Nuevo Cliente');

    await page.fill('#id_nombre', 'Cliente Test Playwright');
    await page.fill('#id_descripcion', 'Cliente creado desde test');
    await page.locator('button.btn-primary').click();

    await expect(page).toHaveURL('/clientes/');
    await expect(page.locator('.alert-success')).toContainText('creado exitosamente');
    await expect(page.locator('table')).toContainText('Cliente Test Playwright');
  });

  test('edit existing client', async ({ page }) => {
    await page.goto('/clientes/');
    await page.locator('table a[href*="editar"]').first().click();

    await expect(page.locator('.card-header h6')).toContainText('Editar Cliente');
    await page.fill('#id_nombre', 'Codelco Modificado');
    await page.locator('button.btn-primary').click();

    await expect(page).toHaveURL('/clientes/');
    await expect(page.locator('.alert-success')).toContainText('actualizado exitosamente');
    await expect(page.locator('table')).toContainText('Codelco Modificado');
  });

});

test.describe('Centros de Costo', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
  });

  test('cost center list shows seeded centers', async ({ page }) => {
    await page.goto('/centros-costo/');
    await expect(page.locator('h1')).toContainText('Centros de Costo');
    await expect(page.locator('table')).toContainText('RAJO-001');
    await expect(page.locator('table')).toContainText('PLANTA-001');
    await expect(page.locator('table')).toContainText('FUND-001');
  });

  test('create new cost center', async ({ page }) => {
    await page.goto('/centros-costo/nuevo/');
    await expect(page.locator('.card-header h6')).toContainText('Nuevo Centro de Costo');

    await page.fill('#id_nombre', 'CeCo Test Playwright');
    await page.fill('#id_codigo', 'TST-999');
    await page.selectOption('#id_cliente', { index: 1 });
    await page.locator('button.btn-primary').click();

    await expect(page).toHaveURL('/centros-costo/');
    await expect(page.locator('.alert-success')).toContainText('creado exitosamente');
    await expect(page.locator('table')).toContainText('TST-999');
  });

  test('edit cost center name', async ({ page }) => {
    await page.goto('/centros-costo/');
    await page.locator('table a[title="Editar"]').first().click();

    await expect(page.locator('.card-header h6')).toContainText('Editar Centro de Costo');
    await page.fill('#id_nombre', 'Mina Rajo Modificado');
    await page.locator('button.btn-primary').click();

    await expect(page).toHaveURL('/centros-costo/');
    await expect(page.locator('.alert-success')).toContainText('actualizado exitosamente');
  });

  test('cost center detail shows information', async ({ page }) => {
    await page.goto('/centros-costo/');
    await page.locator('table tbody a[href*="centros-costo"]').first().click();

    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('.card dl')).toContainText('Código');
    await expect(page.locator('.card dl')).toContainText('Cliente');
  });

  test('toggle cost center status', async ({ page }) => {
    await page.goto('/centros-costo/');
    const toggleBtn = page.locator('button[title="Desactivar"], button[title="Reactivar"]').last();
    await expect(toggleBtn).toBeVisible();
    await toggleBtn.click();

    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 10000 });
  });

  test('filter cost centers by status', async ({ page }) => {
    await page.goto('/centros-costo/');
    await page.selectOption('select[name="estado"]', 'inactivo');
    await page.locator('button.btn-primary').click();
    await expect(page).toHaveURL(/estado=inactivo/);
  });

});
