import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Process Actions & Edge Cases', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
  });

  test('Filter processes by both tipo and estado simultaneously', async ({ page }) => {
    // Apply two filters at once and verify the URL contains both params
    await page.goto('/procesos/');
    await page.selectOption('select[name="tipo"]', 'contratacion');
    await page.selectOption('select[name="estado"]', 'en_curso');
    await page.locator('button.btn-primary').click();
    await expect(page).toHaveURL(/tipo=contratacion/);
    await expect(page).toHaveURL(/estado=en_curso/);
  });

  test('Create cambio_ceco process and verify redirect', async ({ page }) => {
    // The cambio_ceco form should submit and redirect to process detail
    await page.goto('/procesos/nuevo/cambio-ceco/');
    await expect(page.locator('.card-header h6')).toContainText('Nuevo Cambio de Centro de Costo');

    await page.selectOption('#id_trabajador', { index: 1 });
    await page.selectOption('#id_ceco_destino', { index: 1 });
    // Fill the date field with a future date
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 7);
    const dateStr = futureDate.toISOString().split('T')[0];
    await page.fill('#id_fecha_estimada', dateStr);
    await page.fill('#id_motivo', 'Cambio por reasignación');
    await page.locator('button.btn-primary').click();

    // Should redirect to the new process detail page
    await expect(page).toHaveURL(/\/procesos\/\d+\//);
    await expect(page.locator('.alert-success')).toContainText('iniciado');
  });

  test('Process detail shows progress bar with task completion percentage', async ({ page }) => {
    // The process detail page should show a progress bar indicating task completion
    await page.goto('/procesos/');
    const firstProcess = page.locator('table a[href*="/procesos/"]').first();
    await expect(firstProcess).toBeVisible({ timeout: 5000 });
    await firstProcess.click();

    // Verify the progress section shows the task count (e.g., "2/4 tareas")
    await expect(page.locator('.card-body')).toContainText(/tareas/);
    // Verify the progress bar element exists
    await expect(page.locator('.progress-bar')).toBeVisible();
  });

  test('Process type select page shows all 5 process types as clickable cards', async ({ page }) => {
    // The process type selection should list all 5 types with clickable links
    await page.goto('/procesos/nuevo/');
    const typeLinks = page.locator('.seleccion-proceso a');
    const count = await typeLinks.count();
    expect(count).toBe(5);  // contratacion, cambio_ceco, termino, despido, asignacion_activos
  });

});
