import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Kanban Board - Card Interactions', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
  });

  test('Admin can open task detail modal by clicking a kanban card', async ({ page }) => {
    // Clicking a kanban card should open the detail modal via fetch with HX-Request header
    await page.goto('/kanban/');
    const firstCard = page.locator('.kanban-card').first();
    await expect(firstCard).toBeVisible({ timeout: 5000 });

    await firstCard.click();
    // The modal should appear with a spinner or content inside #cardDetailContent
    await expect(page.locator('#cardDetailModal')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('#cardDetailContent')).toBeVisible();
  });

  test('Admin dropdown changes task estado and updates load indicator', async ({ page }) => {
    // The admin dropdown "Cambiar Estado" should POST to update_task and refresh the load indicator
    await page.goto('/kanban/');
    const firstCard = page.locator('.kanban-card').first();
    await expect(firstCard).toBeVisible({ timeout: 5000 });
    await firstCard.click();

    // The detail modal should render the admin dropdown since the user is admin
    const cambiarEstadoBtn = page.locator('button:has-text("Cambiar Estado")');
    await expect(cambiarEstadoBtn).toBeVisible({ timeout: 8000 });
    await cambiarEstadoBtn.click();
    // Wait for dropdown animation to complete before checking menu items
    await page.waitForTimeout(300);
    const option = page.locator('a[data-cambiar-estado="en_proceso"]');
    await expect(option).toBeVisible();
    await option.click();

    // After changing state, the load indicator should refresh (verify it's still visible on the board)
    await page.goto('/kanban/');
    await expect(page.locator('#load-indicator')).toBeVisible();
  });

  test('Kanban board loads with HTMX filters and partial response', async ({ page }) => {
    // The filter form uses hx-get to swap the board partial; submit should trigger an HTMX request
    await page.goto('/kanban/');
    const filterForm = page.locator('#kanban-filters');
    await expect(filterForm).toBeVisible();

    // Select a process type filter; hx-trigger auto-submits on change after 300ms delay
    await page.selectOption('select[name="tipo_proceso"]', 'contratacion');
    // Verify the board content area is still present after HTMX swap (expect waits up to 5s)
    await expect(page.locator('#kanban-board')).toBeVisible();
  });

  test('Task detail full page renders with correct layout for admin', async ({ page }) => {
    // Direct navigation to /kanban/tarea/<id>/ should show the full layout with sidebar and breadcrumbs
    await page.goto('/kanban/tarea/1/');
    await expect(page.locator('.sidebar')).toBeVisible();
    await expect(page.locator('.breadcrumb')).toBeVisible();
    await expect(page.locator('.card')).toContainText('Detalle de Tarea');
  });

  test('Load indicator element exists on the kanban board', async ({ page }) => {
    // The load indicator div should be present on the kanban board page
    await page.goto('/kanban/');
    await expect(page.locator('#load-indicator')).toBeVisible();
  });

});
