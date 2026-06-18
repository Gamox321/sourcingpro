import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Logística', () => {

  test('logistica dashboard shows stats and task list', async ({ page }) => {
    // The logistica dashboard should load with stat cards and a task list section
    await loginAs(page, 'logistica');
    await page.goto('/logistica/');
    // Verify stat cards are present with key metrics
    await expect(page.locator('.row.mb-4').first()).toBeVisible();
    const statCards = page.locator('.row.mb-4 .card');
    await expect(statCards.first()).toBeVisible();
    await expect(page.locator('.card-header')).toContainText('Mis Tareas Activas');
  });

  test('devoluciones page shows pending returns list', async ({ page }) => {
    // The devoluciones page should load and show either pending returns or an empty state
    await loginAs(page, 'logistica');
    await page.goto('/logistica/devoluciones/');
    await expect(page.locator('h1')).toContainText('Devoluciones de Activos');

    // Check if there are pending returns or the empty state is shown
    const cards = page.locator('.card.shadow');
    const emptyAlert = page.locator('.alert-success');

    if (await cards.count() > 0) {
      await expect(cards.first()).toBeVisible();
    } else {
      await expect(emptyAlert).toContainText('Sin devoluciones pendientes');
    }
  });

  test('recuperaciones page shows pending recoveries list', async ({ page }) => {
    // The recuperaciones page should load and show either pending recoveries or an empty state
    await loginAs(page, 'logistica');
    await page.goto('/logistica/recuperaciones/');
    await expect(page.locator('h1')).toContainText('Recuperación de Activos');

    const cards = page.locator('.card.shadow');
    const emptyAlert = page.locator('.alert-success');

    if (await cards.count() > 0) {
      await expect(cards.first()).toBeVisible();
    } else {
      await expect(emptyAlert).toContainText('Sin recuperaciones pendientes');
    }
  });

  test('inventario page loads with filter form and asset table', async ({ page }) => {
    // The logistica inventory page should display the filter form and asset list table
    await loginAs(page, 'logistica');
    await page.goto('/logistica/inventario/');

    // Verify the page heading
    await expect(page.locator('h1')).toContainText('Inventario de Activos');

    // Verify filter form elements are present
    await expect(page.locator('input[name="q"]')).toBeVisible();
    await expect(page.locator('select[name="estado"]')).toBeVisible();
    await expect(page.locator('select[name="tipo"]')).toBeVisible();
    await expect(page.locator('button.btn-primary')).toBeVisible();

    // Verify the asset table or an empty state is displayed
    const table = page.locator('table');
    const emptyState = page.locator('.alert-info');
    if (await table.isVisible()) {
      await expect(table.locator('thead')).toBeVisible();
    } else {
      await expect(emptyState).toContainText('Sin resultados');
    }
  });

  test('tablero shows three column board structure', async ({ page }) => {
    // The logistica tablero page should show Pendientes, En Proceso, and Completadas columns
    await loginAs(page, 'logistica');
    await page.goto('/logistica/tablero/');

    await expect(page.locator('h6:has-text("Pendientes")')).toBeVisible();
    await expect(page.locator('h6:has-text("En Proceso")')).toBeVisible();
    await expect(page.locator('h6:has-text("Completadas")')).toBeVisible();
  });

});
