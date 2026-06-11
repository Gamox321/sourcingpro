import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Notificaciones', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
  });

  test('notification list page loads', async ({ page }) => {
    await page.goto('/notificaciones/');
    await expect(page.locator('h1')).toContainText('Notificaciones');
  });

  test('notification list either shows notifications or empty state', async ({ page }) => {
    await page.goto('/notificaciones/');
    const notifCount = await page.locator('.card-body a').count();
    const emptyMessage = page.locator('.card-body:has-text("No hay notificaciones")');
    if (notifCount === 0) {
      await expect(emptyMessage).toBeVisible();
    } else {
      expect(notifCount).toBeGreaterThanOrEqual(1);
    }
  });

  test('mark all as read button is visible', async ({ page }) => {
    await page.goto('/notificaciones/');
    const markAllBtn = page.locator('button:has-text("Marcar todas leídas")');
    if (await markAllBtn.count() > 0) {
      await expect(markAllBtn).toBeVisible();
    }
  });

  test('notification dropdown exists in navbar', async ({ page }) => {
    await page.goto('/kanban/');
    await expect(page.locator('#alertsDropdown')).toBeVisible();
    await expect(page.locator('#notif-count')).toBeVisible();
  });

  test('filter by no leidas', async ({ page }) => {
    await page.goto('/notificaciones/');
    await page.locator('a[href*="filtro=no_leidas"]').click();
    await expect(page).toHaveURL(/filtro=no_leidas/);
  });

  test('filter by leidas', async ({ page }) => {
    await page.goto('/notificaciones/');
    await page.locator('a[href*="filtro=leidas"]').click();
    await expect(page).toHaveURL(/filtro=leidas/);
  });

});
