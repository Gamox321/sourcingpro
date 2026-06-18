import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Inventario', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
  });

  test('asset list shows seeded assets', async ({ page }) => {
    await page.goto('/inventario/');
    await expect(page.locator('h1')).toContainText('Inventario');
    await expect(page.locator('table')).toContainText('TI-001');
    await expect(page.locator('table')).toContainText('TI-002');
  });

  test('create new asset', async ({ page }) => {
    await page.goto('/inventario/nuevo/');
    await expect(page.locator('.card-header h6')).toContainText('Nuevo Activo');

    const assetCode = 'TST-' + Date.now().toString(36).toUpperCase();

    await page.selectOption('#id_tipo', { index: 1 });
    await page.fill('#id_codigo', assetCode);
    await page.fill('#id_nombre', 'Activo de Prueba');
    await page.locator('button.btn-primary').click();

    await expect(page).toHaveURL('/inventario/');
    await expect(page.locator('.alert-success')).toContainText('registrado exitosamente');
    await expect(page.locator('table')).toContainText(assetCode);
  });

  test('edit existing asset', async ({ page }) => {
    await page.goto('/inventario/');
    await page.locator('table a[title="Editar"]').first().click();

    await expect(page.locator('.card-header h6')).toContainText('Editar Activo');
    await page.fill('#id_nombre', 'Notebook Dell Modificado');
    await page.locator('button.btn-primary').click();

    await expect(page).toHaveURL('/inventario/');
    await expect(page.locator('.alert-success')).toContainText('actualizado exitosamente');
    await expect(page.locator('table')).toContainText('Notebook Dell Modificado');
  });

  test('asset detail shows information', async ({ page }) => {
    await page.goto('/inventario/');
    await page.locator('table a[title="Ver"]').first().click();

    await expect(page.locator('h1')).toBeVisible();
    const statCards = page.locator('.row .card');
    await expect(statCards.first()).toContainText('Estado');
  });

  test('search asset by code', async ({ page }) => {
    await page.goto('/inventario/');
    await page.fill('input[name="q"]', 'TI-001');
    await page.locator('button.btn-primary').click();
    await expect(page.locator('table')).toContainText('TI-001');
  });

  test('filter assets by estado', async ({ page }) => {
    await page.goto('/inventario/');
    await page.selectOption('select[name="estado"]', 'disponible');
    await page.locator('button.btn-primary').click();
    await expect(page).toHaveURL(/estado=disponible/);
  });

});
