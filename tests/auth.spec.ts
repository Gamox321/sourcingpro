import { test, expect } from '@playwright/test';
import { loginAs, loginAsRaw, logout, expectFlashMessage } from './helpers';

test.describe('Autenticación', () => {

  test('admin login redirects to kanban board', async ({ page }) => {
    await loginAs(page, 'admin');
    await expect(page).toHaveURL('/kanban/');
    await expect(page.locator('.sidebar-brand')).toBeVisible();
    await expect(page.locator('h1')).toContainText('Tablero Kanban');
  });

  test('rrhh login redirects to rrhh dashboard', async ({ page }) => {
    await loginAs(page, 'rrhh');
    await expect(page).toHaveURL('/rrhh/');
  });

  test('ti login redirects to ti dashboard', async ({ page }) => {
    await loginAs(page, 'ti');
    await expect(page).toHaveURL('/ti/');
  });

  test('jefatura login redirects to jefatura nomina', async ({ page }) => {
    await loginAs(page, 'jefatura');
    await expect(page).toHaveURL('/jefatura/');
  });

  test('prevencion login redirects to prevencion dashboard', async ({ page }) => {
    await loginAs(page, 'prevencion');
    await expect(page).toHaveURL('/prevencion/');
  });

  test('finanzas login redirects to finanzas dashboard', async ({ page }) => {
    await loginAs(page, 'finanzas');
    await expect(page).toHaveURL('/finanzas/');
  });

  test('logistica login redirects to logistica dashboard', async ({ page }) => {
    await loginAs(page, 'logistica');
    await expect(page).toHaveURL('/logistica/');
  });

  test('failed login shows error message', async ({ page }) => {
    await loginAsRaw(page, 'admin@sourcingpro.cl', 'wrongpassword');
    await expect(page.locator('.alert')).toBeVisible();
    await expect(page).toHaveURL('/login/');
  });

  test('unknown email shows generic error', async ({ page }) => {
    await loginAsRaw(page, 'noexiste@test.cl', 'SomePass1!');
    await expect(page.locator('.alert-danger')).toContainText(
      'Correo electrónico o contraseña incorrectos'
    );
  });

  test('logout redirects to login page', async ({ page }) => {
    await loginAs(page, 'admin');
    await logout(page);
    await expect(page).toHaveURL('/login/');
    await expect(page.locator('h1')).toContainText('SourcingPro');
  });

  test('unauthenticated user is redirected to login', async ({ page }) => {
    await page.goto('/kanban/');
    await expect(page).toHaveURL('/login/');
  });

  test('unauthenticated user cannot access admin pages', async ({ page }) => {
    await page.goto('/usuarios/');
    await expect(page).toHaveURL('/login/');
  });

});
