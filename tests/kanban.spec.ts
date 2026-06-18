import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Kanban Board', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
  });

  test('board displays three columns: Pendientes, En Proceso, Completadas', async ({ page }) => {
    // The kanban board should have exactly 3 columns with correct column headers
    await page.goto('/kanban/');
    await expect(page.locator('h1')).toContainText('Tablero Kanban');
    await expect(page.locator('.kanban-column')).toHaveCount(3);
    await expect(page.locator('.kanban-board .card-header').first()).toContainText('Pendientes');
    await expect(page.locator('.kanban-board .card-header').nth(1)).toContainText('En Proceso');
    await expect(page.locator('.kanban-board .card-header').nth(2)).toContainText('Completadas');
  });

  test('board shows summary stat cards with key metrics', async ({ page }) => {
    // The board should display summary statistics: active processes and pending tasks
    await page.goto('/kanban/');
    const statRow = page.locator('.row.mb-3').first();
    await expect(statRow.locator('.card').first()).toContainText('Procesos activos');
    await expect(statRow.locator('.card').nth(1)).toContainText('Tareas pendientes');
  });

  test('kanban cards show process type badge', async ({ page }) => {
    // Each kanban card should display a badge with the process type (contratacion, termino, etc.)
    await page.goto('/kanban/');
    const cards = page.locator('.kanban-card');
    const count = await cards.count();
    // Verify at least one card exists and that it has a badge
    expect(count).toBeGreaterThanOrEqual(1);
    const firstCardBadges = cards.first().locator('.badge');
    expect(await firstCardBadges.count()).toBeGreaterThanOrEqual(1);
  });

  test('filter form elements are present', async ({ page }) => {
    // The board should have a filter form with process type, area, search, and clear filters
    await page.goto('/kanban/');
    await expect(page.locator('select[name="tipo_proceso"]')).toBeVisible();
    await expect(page.locator('select[name="area"]')).toBeVisible();
    await expect(page.locator('input[name="q"]')).toBeVisible();
    await expect(page.locator('a[href="/kanban/"]')).toBeVisible();
  });

  test('search input accepts text', async ({ page }) => {
    // The search field should be functional and accept text input
    await page.goto('/kanban/');
    const input = page.locator('input[name="q"]');
    await expect(input).toBeVisible();
    await input.fill('Camila');
    await expect(input).toHaveValue('Camila');
  });

  test('clear filters link reloads the board without query params', async ({ page }) => {
    // Clicking the "Limpiar filtros" link should reset the URL to the base kanban page
    await page.goto('/kanban/?tipo_proceso=contratacion');
    await expect(page.locator('select[name="tipo_proceso"]')).toHaveValue('contratacion');
    await page.locator('a[href="/kanban/"]').first().click();
    await expect(page).toHaveURL('/kanban/');
  });

});
