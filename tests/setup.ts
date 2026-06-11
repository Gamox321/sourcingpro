import { execSync } from 'child_process';
import path from 'path';

async function globalSetup() {
  const venv = path.join(__dirname, '..', 'venv', 'Scripts', 'python.exe');
  const managePy = path.join(__dirname, '..', 'manage.py');
  const cwd = path.join(__dirname, '..');

  const cmds = [
    `${venv} ${managePy} flush --no-input`,
    `${venv} ${managePy} migrate`,
    `${venv} ${managePy} bootstrap_admin`,
    `${venv} ${managePy} seed_clients`,
    `${venv} ${managePy} seed_notifications`,
    `${venv} ${managePy} shell -c "from apps.accounts.models import Role; [Role.objects.get_or_create(nombre=r) for r in ['rrhh','ti','jefatura','prevencion','finanzas','logistica']]"`,
    `${venv} ${managePy} shell -c "from apps.inventory.models import AssetType; [AssetType.objects.get_or_create(nombre=n, defaults={'descripcion': d, 'es_personalizado': False}) for n, d in [('Equipos TI', 'Equipos tecnológicos'), ('EPP', 'Elementos de protección personal'), ('Vehículos', 'Vehículos'), ('Herramientas', 'Herramientas')]]"`,
    `${venv} ${managePy} seed_demo`,
  ];

  for (const cmd of cmds) {
    execSync(cmd, { stdio: 'inherit', cwd });
  }
}

export default globalSetup;
