import { test, expect } from '@playwright/test';
import { loginAs } from './helpers';

test.describe('Procesos', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
  });

  test('process list shows seeded processes', async ({ page }) => {
    await page.goto('/procesos/');
    await expect(page.locator('h1')).toContainText('Procesos');
    await expect(page.locator('table')).toContainText('Camila Reyes');
    await expect(page.locator('table')).toContainText('Roberto Díaz');
  });

  test('process type select page shows options', async ({ page }) => {
    await page.goto('/procesos/nuevo/');
    await expect(page.locator('h1')).toContainText('Seleccionar Tipo de Proceso');
    await expect(page.locator('.seleccion-proceso')).toContainText('Contratacion');
    await expect(page.locator('.seleccion-proceso')).toContainText('Despido');
  });

  test('create contratacion process', async ({ page }) => {
    await page.goto('/procesos/nuevo/contratacion/');
    await expect(page.locator('.card-header h6')).toContainText('Nueva Contratacion');

    await page.fill('#id_run', '33333333-3');
    await page.fill('#id_nombre', 'Contratado Test Playwright');
    await page.fill('#id_correo', 'contratado.test@sourcingpro.cl');
    await page.fill('#id_cargo', 'Operario de Prueba');
    await page.selectOption('#id_centro_costo', { index: 1 });
    await page.locator('button.btn-primary').click();

    await expect(page).toHaveURL(/\/procesos\/\d+\//);
    await expect(page.locator('.alert-success')).toContainText('iniciado exitosamente');
    await expect(page.locator('h1')).toContainText('Contratado Test Playwright');
  });

  test('process detail shows tasks', async ({ page }) => {
    await page.goto('/procesos/');
    await page.locator('table td a[href*="procesos/"]').first().click();

    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('.card-header').first()).toContainText('Tareas');
  });

  test('filter processes by type', async ({ page }) => {
    await page.goto('/procesos/');
    await page.selectOption('select[name="tipo"]', 'contratacion');
    await page.locator('button.btn-primary').click();
    await expect(page).toHaveURL(/tipo=contratacion/);
  });

  test('filter processes by estado', async ({ page }) => {
    await page.goto('/procesos/');
    await page.selectOption('select[name="estado"]', 'en_curso');
    await page.locator('button.btn-primary').click();
    await expect(page).toHaveURL(/estado=en_curso/);
  });

  test('complete a task from process detail', async ({ page }) => {
    await page.goto('/procesos/');
    const procesoTd = page.locator('table a[href*="procesos/"][href$="/"]').first();
    await procesoTd.click();

    const completarBtn = page.locator('button.btn-success:has-text("Completar")').first();
    if (await completarBtn.isEnabled()) {
      await completarBtn.click();
      await page.locator('#confirmModalBtn').click();
      await expect(page.locator('.alert-success')).toContainText('completada');
    }
  });

  test('create asignacion de activos process', async ({ page }) => {
    await page.goto('/procesos/nuevo/asignacion-activos/');
    await expect(page.locator('.card-header h6')).toContainText('Asignacion de Activos TI');
    await page.selectOption('#id_trabajador', { index: 1 });
    await page.fill('#id_comentario', 'Notebook para terreno');
    await page.locator('button.btn-primary').click();
    await expect(page).toHaveURL(/\/procesos\/\d+\//);
    await expect(page.locator('.alert-success')).toContainText('iniciado');
    await expect(page.locator('table')).toContainText('Asignaci');
  });

  test('asignacion activos appears in type select', async ({ page }) => {
    await page.goto('/procesos/nuevo/');
    await expect(page.locator('.seleccion-proceso')).toContainText('Asignacion de Activos TI');
    const cardCount = await page.locator('.seleccion-proceso .card').count();
    expect(cardCount).toBeGreaterThanOrEqual(5);
  });

});
