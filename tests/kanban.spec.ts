import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Kanban Board', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
  });

  test('board displays three columns', async ({ page }) => {
    await page.goto('/kanban/');
    await expect(page.locator('h1')).toContainText('Tablero Kanban');
    await expect(page.locator('.kanban-column')).toHaveCount(3);
    await expect(page.locator('.card-header').first()).toContainText('Pendientes');
    await expect(page.locator('.card-header').nth(1)).toContainText('En Proceso');
    await expect(page.locator('.card-header').nth(2)).toContainText('Completadas');
  });

  test('board shows summary stat cards', async ({ page }) => {
    await page.goto('/kanban/');
    const statRow = page.locator('.row.mb-3').first();
    await expect(statRow.locator('.card').first()).toContainText('Procesos activos');
    await expect(statRow.locator('.card').nth(1)).toContainText('Tareas pendientes');
  });

  test('kanban cards show process type badge', async ({ page }) => {
    await page.goto('/kanban/');
    const cards = page.locator('.kanban-card');
    const count = await cards.count();
    if (count > 0) {
      const firstCardBadges = cards.first().locator('.badge');
      expect(await firstCardBadges.count()).toBeGreaterThanOrEqual(1);
    }
  });

  test('filter form elements are present', async ({ page }) => {
    await page.goto('/kanban/');
    await expect(page.locator('select[name="tipo_proceso"]')).toBeVisible();
    await expect(page.locator('select[name="area"]')).toBeVisible();
    await expect(page.locator('input[name="q"]')).toBeVisible();
    await expect(page.locator('a[href="/kanban/"]')).toBeVisible();
  });

  test('search input is functional', async ({ page }) => {
    await page.goto('/kanban/');
    const input = page.locator('input[name="q"]');
    await expect(input).toBeVisible();
    await input.fill('Camila');
    await expect(input).toHaveValue('Camila');
  });

  test('clear filters link reloads board', async ({ page }) => {
    await page.goto('/kanban/?tipo_proceso=contratacion');
    await expect(page.locator('select[name="tipo_proceso"]')).toHaveValue('contratacion');
    await page.locator('a[href="/kanban/"]').first().click();
    await expect(page).toHaveURL('/kanban/');
  });

});
