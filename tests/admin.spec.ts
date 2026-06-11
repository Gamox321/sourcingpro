import { test, expect } from '@playwright/test';
import { loginAs, logout } from './helpers';

test.describe('Administración de Usuarios', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
  });

  test('user list shows all users', async ({ page }) => {
    await page.goto('/usuarios/');
    await expect(page.locator('h1')).toContainText('Usuarios');
    await expect(page.locator('table')).toBeVisible();
  });

  test('create new user', async ({ page }) => {
    await page.goto('/usuarios/nuevo/');
    await expect(page.locator('.card-header h6')).toContainText('Nuevo Usuario');

    await page.fill('#id_email', 'testuser@sourcingpro.cl');
    await page.fill('#id_nombre', 'Usuario Test');
    await page.fill('#id_password1', 'TestPass1!');
    await page.fill('#id_password2', 'TestPass1!');
    await page.locator('input[type="checkbox"][name="roles"]').first().check();
    await page.locator('button.btn-primary').click();

    await expect(page).toHaveURL('/usuarios/');
    await expect(page.locator('.alert-success')).toContainText('creado exitosamente');
    await expect(page.locator('table')).toContainText('testuser@sourcingpro.cl');
  });

  test('edit existing user', async ({ page }) => {
    await page.goto('/usuarios/');
    await page.locator('table a[href*="editar"]').first().click();

    await expect(page.locator('.card-header h6')).toContainText('Editar Usuario');
    await page.fill('#id_nombre', 'Admin Modificado');
    await page.locator('button.btn-primary').click();

    await expect(page).toHaveURL('/usuarios/');
    await expect(page.locator('.alert-success')).toContainText('actualizado exitosamente');
  });

  test('search users by email', async ({ page }) => {
    await page.goto('/usuarios/');
    await page.fill('input[name="q"]', 'admin');
    await page.locator('button.btn-primary').click();
    await expect(page.locator('table')).toContainText('admin@sourcingpro.cl');
  });

  test('non-admin user sees 403 on user list', async ({ page }) => {
    await logout(page);
    await loginAs(page, 'rrhh');
    await page.goto('/usuarios/');
    await expect(page.locator('#page-top')).toContainText('Acceso Denegado');
  });

});
