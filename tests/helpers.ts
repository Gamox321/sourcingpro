import { Page, expect } from '@playwright/test';

const CREDENTIALS: Record<string, { email: string; password: string; redirect: string }> = {
  admin:      { email: 'admin@sourcingpro.cl',      password: 'Admin2024!', redirect: '/kanban/' },
  rrhh:       { email: 'rrhh@sourcingpro.cl',       password: 'Demo2024!',  redirect: '/rrhh/' },
  ti:         { email: 'ti@sourcingpro.cl',         password: 'Demo2024!',  redirect: '/ti/' },
  jefatura:   { email: 'jefatura@sourcingpro.cl',   password: 'Demo2024!',  redirect: '/jefatura/' },
  prevencion: { email: 'prevencion@sourcingpro.cl', password: 'Demo2024!',  redirect: '/prevencion/' },
  finanzas:   { email: 'finanzas@sourcingpro.cl',   password: 'Demo2024!',  redirect: '/finanzas/' },
  logistica:  { email: 'logistica@sourcingpro.cl',  password: 'Demo2024!',  redirect: '/logistica/' },
};

export async function loginAs(page: Page, role: string) {
  const creds = CREDENTIALS[role];
  if (!creds) throw new Error(`Unknown role: ${role}`);
  await page.goto('/login/');
  await page.fill('#id_username', creds.email);
  await page.fill('#id_password', creds.password);
  await page.click('button[type="submit"]');
  await page.waitForURL(`**${creds.redirect}**`);
}

export async function loginAsRaw(page: Page, email: string, password: string) {
  await page.goto('/login/');
  await page.fill('#id_username', email);
  await page.fill('#id_password', password);
  await page.click('button[type="submit"]');
}

export async function logout(page: Page) {
  await page.click('#userDropdown');
  await page.click('button.dropdown-item:has-text("Cerrar sesión")');
  await page.waitForURL('/login/');
}

export async function expectFlashMessage(page: Page, message: string) {
  await expect(page.locator('.alert').filter({ hasText: message })).toBeVisible();
}
