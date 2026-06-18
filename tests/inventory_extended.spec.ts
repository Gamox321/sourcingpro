import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Inventory - Extended Fields', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
  });

  test('Create asset with marca, modelo, numero_serie saves and displays correctly', async ({ page }) => {
    // The new fields (marca, modelo, numero_serie) should be saved when creating an asset
    const assetCode = 'EXT-' + Date.now().toString(36).toUpperCase();

    await page.goto('/inventario/nuevo/');
    await expect(page.locator('.card-header h6')).toContainText('Nuevo Activo');

    await page.selectOption('#id_tipo', { index: 1 });
    await page.fill('#id_codigo', assetCode);
    await page.fill('#id_nombre', 'Asset Extended Test');
    await page.fill('#id_marca', 'Dell');
    await page.fill('#id_modelo', 'Latitude 5520');
    await page.fill('#id_numero_serie', 'SN-' + assetCode);
    await page.locator('button.btn-primary').click();

    // Verify redirect and success
    await expect(page).toHaveURL('/inventario/');
    await expect(page.locator('.alert-success')).toContainText('registrado exitosamente');
    await expect(page.locator('table')).toContainText(assetCode);
  });

  test('Create asset without optional fields marca, modelo, numero_serie still succeeds', async ({ page }) => {
    // The new fields are blank=True - they should be optional and not block submission
    const assetCode = 'OPT-' + Date.now().toString(36).toUpperCase();

    await page.goto('/inventario/nuevo/');
    await expect(page.locator('.card-header h6')).toContainText('Nuevo Activo');

    await page.selectOption('#id_tipo', { index: 1 });
    await page.fill('#id_codigo', assetCode);
    await page.fill('#id_nombre', 'Asset Optional Test');
    // Intentionally NOT filling marca, modelo, numero_serie
    await page.locator('button.btn-primary').click();

    // Verify the asset is still created successfully (optional fields should not cause validation errors)
    await expect(page).toHaveURL('/inventario/');
    await expect(page.locator('.alert-success')).toContainText('registrado exitosamente');
    await expect(page.locator('table')).toContainText(assetCode);
  });

  test('Edit asset modifies marca, modelo, numero_serie fields', async ({ page }) => {
    // Editing an asset should allow changing the new fields
    const assetCode = 'EDT-' + Date.now().toString(36).toUpperCase();

    // First create an asset without the fields
    await page.goto('/inventario/nuevo/');
    await page.selectOption('#id_tipo', { index: 1 });
    await page.fill('#id_codigo', assetCode);
    await page.fill('#id_nombre', 'To Edit');
    await page.locator('button.btn-primary').click();
    await expect(page.locator('.alert-success')).toContainText('registrado exitosamente');

    // Now go to edit it
    await page.goto('/inventario/');
    await page.fill('input[name="q"]', assetCode);
    await page.locator('button.btn-primary').click();
    await page.locator('table a[title="Editar"]').first().click();

    await expect(page.locator('.card-header h6')).toContainText('Editar Activo');
    await page.fill('#id_marca', 'HP');
    await page.fill('#id_modelo', 'ProBook 450');
    await page.fill('#id_numero_serie', 'HP-SN-001');
    await page.locator('button.btn-primary').click();

    // Verify the edit saved
    await expect(page).toHaveURL('/inventario/');
    await expect(page.locator('.alert-success')).toContainText('actualizado exitosamente');
  });

});
