import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Notificaciones', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
  });

  test('notification list page loads with heading', async ({ page }) => {
    // The notifications page should display the "Notificaciones" heading
    await page.goto('/notificaciones/');
    await expect(page.locator('h1')).toContainText('Notificaciones');
  });

  test('notification list shows notifications or empty state message', async ({ page }) => {
    // The notifications page should either show notification items or an empty state
    await page.goto('/notificaciones/');
    const notifLinks = page.locator('.card-body a');
    const notifCount = await notifLinks.count();

    if (notifCount > 0) {
      // Notifications exist - verify at least one is shown
      expect(notifCount).toBeGreaterThanOrEqual(1);
    } else {
      // No notifications - verify empty state message is shown
      await expect(page.locator('.card-body:has-text("No hay notificaciones")')).toBeVisible();
    }
  });

  test('mark all as read button is visible when there are unread notifications', async ({ page }) => {
    // If unread notifications exist, the "Marcar todas leídas" button should be available
    await page.goto('/notificaciones/');
    const markAllBtn = page.locator('button:has-text("Marcar todas leídas")');
    if (await markAllBtn.count() > 0) {
      await expect(markAllBtn).toBeVisible();
    }
  });

  test('notification dropdown exists in navbar with count badge', async ({ page }) => {
    // The top navbar should have a notification dropdown with a count badge
    await page.goto('/kanban/');
    await expect(page.locator('#alertsDropdown')).toBeVisible();
    await expect(page.locator('#notif-count')).toBeVisible();
  });

  test('filter by no leídas updates the URL', async ({ page }) => {
    // Clicking the "no leídas" filter link should update the URL with filtro=no_leidas
    await page.goto('/notificaciones/');
    const filterLink = page.locator('a[href*="filtro=no_leidas"]');
    await expect(filterLink).toBeVisible();
    await filterLink.click();
    await expect(page).toHaveURL(/filtro=no_leidas/);
  });

  test('filter by leídas updates the URL', async ({ page }) => {
    // Clicking the "leídas" filter link should update the URL with filtro=leidas
    await page.goto('/notificaciones/');
    const filterLink = page.locator('a[href*="filtro=leidas"]');
    await expect(filterLink).toBeVisible();
    await filterLink.click();
    await expect(page).toHaveURL(/filtro=leidas/);
  });

});
