import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Trabajadores', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
  });

  test('worker list shows seeded workers', async ({ page }) => {
    await page.goto('/trabajadores/');
    await expect(page.locator('h1')).toContainText('Trabajadores');
    await expect(page.locator('table')).toContainText('Juan Pérez');
    await expect(page.locator('table')).toContainText('María Soto');
  });

  test('create new worker', async ({ page }) => {
    await page.goto('/trabajadores/nuevo/');
    await expect(page.locator('.card-header h6')).toContainText('Nuevo Trabajador');

    await page.fill('#id_run', '22222222-2');
    await page.fill('#id_nombre', 'Trabajador Test Playwright');
    await page.fill('#id_correo', 'testworker@sourcingpro.cl');
    await page.fill('#id_cargo', 'Operario de Prueba');
    await page.selectOption('#id_centro_costo_actual', { index: 1 });
    await page.locator('button.btn-primary').click();

    await expect(page).toHaveURL('/trabajadores/');
    await expect(page.locator('.alert-success')).toContainText('registrado exitosamente');
    await expect(page.locator('table')).toContainText('Trabajador Test Playwright');
  });

  test('edit existing worker', async ({ page }) => {
    await page.goto('/trabajadores/');
    await page.locator('table a[title="Editar"]').first().click();

    await expect(page.locator('.card-header h6')).toContainText('Editar Trabajador');
    await page.fill('#id_nombre', 'Juan Pérez Modificado');
    await page.locator('button.btn-primary').click();

    await expect(page).toHaveURL('/trabajadores/');
    await expect(page.locator('.alert-success')).toContainText('actualizado exitosamente');
    await expect(page.locator('table')).toContainText('Juan Pérez Modificado');
  });

  test('worker detail shows information', async ({ page }) => {
    await page.goto('/trabajadores/');
    await page.locator('table a[title="Ficha"]').first().click();

    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('dl')).toContainText('RUN');
    await expect(page.locator('dl')).toContainText('Nombre completo');
  });

  test('search worker by name', async ({ page }) => {
    await page.goto('/trabajadores/');
    await page.fill('input[name="q"]', 'Juan');
    await page.locator('button.btn-primary').click();
    await expect(page.locator('table')).toContainText('Juan Pérez');
  });

  test('filter workers by estado', async ({ page }) => {
    await page.goto('/trabajadores/');
    await page.selectOption('select[name="estado"]', 'activo');
    await page.locator('button.btn-primary').click();
    await expect(page).toHaveURL(/estado=activo/);
  });

});
