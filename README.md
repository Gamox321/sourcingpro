# SourcingPro - Sistema de Gestión del Ciclo de Vida del Trabajador

## 📋 Descripción

SourcingPro es un sistema desarrollado para **Sourcing SPA**, empresa de servicios a la industria minera en Chile. El sistema centraliza y automatiza la gestión del ciclo de vida del trabajador, eliminando la coordinación manual entre las áreas de Recursos Humanos, TI, Finanzas, Logística y Prevención de Riesgos.

---

## 🔐 Credenciales de Acceso

### Usuarios de Prueba

| Rol | Email | Contraseña | Nombre | URL Redirección |
|-----|-------|------------|--------|-----------------|
| **Administrador** | `admin@sourcingpro.cl` | `Admin2024!` | Administrador | `/kanban/` |
| **RRHH** | `rrhh@sourcingpro.cl` | `Demo2024!` | María González | `/rrhh/` |
| **Jefatura** | `jefatura@sourcingpro.cl` | `Demo2024!` | Carlos Muñoz | `/jefatura/` |
| **TI** | `ti@sourcingpro.cl` | `Demo2024!` | Pedro Ramírez | `/ti/` |
| **Prevención** | `prevencion@sourcingpro.cl` | `Demo2024!` | Ana Soto | `/prevencion/` |
| **Finanzas** | `finanzas@sourcingpro.cl` | `Demo2024!` | Luis Torres | `/finanzas/` |
| **Logística** | `logistica@sourcingpro.cl` | `Demo2024!` | Daniela Vega | `/logistica/` |

> **Nota:** La contraseña de administrador se establece al ejecutar el comando `bootstrap_admin`.

---

## 🚀 Inicio del Sistema

### 1. Activar Entorno Virtual

```bash
cd C:\sourcingpro-main
.\venv\Scripts\Activate.ps1
```

### 2. Iniciar Servidor de Desarrollo

```bash
python manage.py runserver
```

### 3. Acceder al Sistema

Navega a: `http://127.0.0.1:8000/`

El sistema redirigirá automáticamente al dashboard correspondiente según el rol del usuario.

---

## 📊 Módulos del Sistema

### RRHH (Recursos Humanos)
- **Dashboard** - `/rrhh/`
- **Trabajadores** - `/rrhh/trabajadores/`
- **Procesos** - `/rrhh/procesos/`
- **Detalle de Proceso** - `/rrhh/procesos/<id>/`
- **Centros de Costo** - `/rrhh/cecos/`
- **Configuración de Plazos** - `/rrhh/configuracion/plazos/`
- **Alertas de Contratos por Vencer** - `/rrhh/alertas/contratos/`
- **Reportes** - `/rrhh/reportes/`

### TI (Tecnología de la Información)
- **Dashboard** - `/ti/`
- **Inventario TI** - `/ti/inventario/`
- **Crear Equipo TI** - `/ti/inventario/nuevo/`
- **Tablero Kanban** - `/ti/tablero/`
- **Bloqueo Urgente** - `/ti/bloqueo-urgente/` (para despidos)

### Prevención de Riesgos
- **Dashboard** - `/prevencion/`
- **Inventario EPP** - `/prevencion/inventario/`
- **Certificaciones** - `/prevencion/certificaciones/`
- **Tablero General** - `/prevencion/tablero/`

### Jefatura
- **Mi Nómina** - `/jefatura/nomina/`
- **Detalle Trabajador** - `/jefatura/trabajador/<id>/`
- **Tablero Kanban** - `/jefatura/tablero/`
- **Procesos** - `/jefatura/procesos/`
- **Mi CeCo** - `/jefatura/ceco/`

### Finanzas
- **Dashboard** - `/finanzas/`
- **Finiquitos** - `/finanzas/finiquitos/`
- **Tablero Kanban** - `/finanzas/tablero/`

### Logística
- **Dashboard** - `/logistica/`
- **Devoluciones** - `/logistica/devoluciones/`
- **Recuperaciones** - `/logistica/recuperaciones/`
- **Inventario** - `/logistica/inventario/`
- **Tablero Kanban** - `/logistica/tablero/`

---

## 🔄 Procesos Principales

### 1. Contratación
- Inicio por RRHH/Jefatura
- Tareas paralelas: TI (cuenta), Prevención (exámenes/EPP), Logística (equipamiento)
- Cierre automático cuando todas las tareas están completadas
- Trabajador pasa a estado "Activo"

### 2. Cambio de Centro de Costo
- Inicio por RRHH/Jefatura
- Validación de activos asignados
- Devolución obligatoria antes de avanzar (RF-13)
- Reincorporación simplificada en nuevo CeCo
- Historial de CeCo actualizado automáticamente

### 3. Término de Contrato
- Detección automática de contratos por vencer (RF-19)
- Alertas configurables por trabajador
- Tareas: Logística (devolución), TI (preparar bloqueo), Finanzas (finiquito)
- **Cierre manual por RRHH** (RF-25)
- Bloqueo de accesos tras confirmación

### 4. Despido
- **Bloqueo inmediato de accesos** (RF-29)
- Tarea crítica a TI con plazo reducido
- Recuperación de activos con evidencia fotográfica
- Cierre mixto: automático + confirmación RRHH
- Historial con hora exacta de bloqueo (RF-35)

---

## 🛠️ Comandos de Gestión

### Crear Administrador

```bash
python manage.py bootstrap_admin --email admin@sourcingpro.cl --password Admin2024!
```

### Cargar Datos de Demostración

```bash
python manage.py seed_demo
```

### Configurar Plazos de Tareas por Defecto

```bash
python manage.py seed_task_deadlines
```

### Verificar Tareas Vencidas y Alertas (Job Diario)

```bash
python manage.py verificar_vencidas_y_alertas
```

> **Recomendación:** Configurar este comando en el scheduler del sistema para ejecución diaria a las 8:00 AM.

### Migraciones de Base de Datos

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 📁 Estructura del Proyecto

```
sourcingpro-main/
├── apps/
│   ├── accounts/          # Autenticación y usuarios
│   ├── audit/             # Bitácora de auditoría
│   ├── clients/           # Clientes y centros de costo
│   ├── inventory/         # Activos y asignaciones
│   ├── kanban/            # Vistas por rol (RRHH, TI, Finanzas, Logística, Prevención, Jefatura)
│   ├── notifications/     # Sistema de notificaciones
│   ├── processes/         # Procesos y tareas
│   └── workers/           # Trabajadores
├── config/                # Configuración de Django
├── templates/             # Templates HTML por módulo
├── static/                # Archivos estáticos (CSS, JS)
├── media/                 # Archivos subidos (evidencias)
├── venv/                  # Entorno virtual
├── manage.py
└── README.md
```

---

## 🔔 Sistema de Notificaciones

Las notificaciones están **centralizadas** y son accesibles para todos los roles desde:
- **URL:** `/notificaciones/`
- **Dropdown en navbar:** Icono de campana con contador

### Eventos Notificables

| Evento | Destinatario | Descripción |
|--------|-------------|-------------|
| `proceso_inicio` | Iniciador | Proceso iniciado con tareas generadas |
| `proceso_cierre` | Iniciador | Proceso completado/cancelado |
| `tarea_cambio_estado` | Responsable + Iniciador | Tarea completada/actualizada |
| `tarea_vencida` | Responsable + Jefatura | Tarea vencida (fuera de plazo) |
| `tarea_proxima_vencer` | Responsable | Recordatorio (2 días antes) |
| `tarea_escalada` | Jefatura de área | Tarea escalada por vencimiento |
| `bloqueo_ejecutado` | RRHH | TI confirmó bloqueo en despido |
| `devolucion_validada` | Iniciador | Todos los activos devueltos (cambio CeCo) |
| `devolucion_incompleta` | Iniciador | Activos pendientes de devolución |
| `contrato_por_vencer` | RRHH | Alerta de término de contrato |
---

## 📸 Evidencia Fotográfica

### Devolución y Recuperación de Activos

Los usuarios de **Logística** pueden subir evidencia fotográfica de dos formas:

1. **Archivo Local** (recomendado)
   - Formatos: JPG, PNG, PDF
   - Ubicación: `media/evidencias/activos/`
   - Máximo: 5MB

2. **URL Externa**
   - Pegar URL de imagen (Imgur, Google Drive, etc.)
   - Se ignora si se sube archivo

### Vista de Evidencias

Las fotos/evidencias son visibles en:
- Detalle de proceso: `/rrhh/procesos/<id>/`
- Devoluciones: `/logistica/devoluciones/`
- Recuperaciones: `/logistica/recuperaciones/`

---

## ⚙️ Configuración

### Plazos de Tareas Configurables

RRHH puede configurar los plazos desde: `/rrhh/configuracion/plazos/`

**Valores por defecto:**

| Tipo de Tarea | Plazo (días) | Escalamiento (días) | Crítica |
|--------------|--------------|---------------------|---------|
| Creación de cuenta TI | 3 | 1 | No |
| Exámenes preocupacionales | 5 | 2 | No |
| EPP e Inducción | 3 | 1 | No |
| Equipamiento | 5 | 2 | No |
| Devolución de activos | 5 | 2 | No |
| Recuperación de activos | 3 | 1 | **Sí** |
| Preparar bloqueo de accesos | 2 | 1 | **Sí** |
| Bloqueo de accesos | 1 | 0 | **Sí** |
| Coordinación de finiquito | 5 | 2 | No |

---

## 📝 Requerimientos Funcionales Implementados

### Módulo de Contratación (RF-01 a RF-09) ✅
- RF-01: Iniciar proceso de contratación
- RF-02: Generación automática de tareas en paralelo
- RF-03: Asignación de responsable por tarea
- RF-04: Seguimiento del estado de tareas
- RF-05: Registro de entrega de implementos y equipamiento
- RF-06: Cierre del proceso de contratación
- **RF-07: Escalamiento por tarea vencida** (con plazos configurables)
- **RF-08: Historial del proceso** (bitácora de auditoría)
- RF-09: Notificaciones automáticas

### Módulo de Cambio de Centro de Costo (RF-10 a RF-18) ✅
- RF-10: Iniciar proceso de cambio de centro de costo
- RF-11: Verificación automática de activos pendientes
- RF-12: Gestión de devolución de activos
- **RF-13: Bloqueo del proceso ante devolución incompleta**
- RF-14: Validación y cierre de la devolución
- RF-15: Reinicio simplificado del flujo de contratación
- RF-16: Cierre del proceso de cambio de centro de costo
- **RF-17: Historial del proceso de cambio**
- RF-18: Notificaciones automáticas del proceso

### Módulo de Término de Contrato (RF-19 a RF-27) ✅
- **RF-19: Detección automática de contratos próximos a vencer**
- RF-20: Iniciar proceso de término de contrato
- RF-21: Generación automática de tareas en paralelo
- **RF-22: Gestión simplificada de devolución de activos (con fotos)**
- RF-23: Recordatorio de coordinación de finiquito
- RF-24: Escalamiento por tarea vencida
- **RF-25: Cierre manual del proceso y bloqueo de accesos**
- **RF-26: Historial del proceso de término**
- RF-27: Notificaciones automáticas del proceso

### Módulo de Despido (RF-28 a RF-36) ✅
- RF-28: Iniciar proceso de despido
- **RF-29: Bloqueo inmediato de accesos** (UI urgente para TI)
- RF-30: Generación automática de tareas en paralelo
- **RF-31: Gestión de recuperación de activos (con fotos)**
- RF-32: Recordatorio de coordinación de finiquito y descuentos
- **RF-33: Escalamiento por tarea vencida (plazo reducido para críticas)**
- RF-34: Cierre mixto del proceso
- **RF-35: Historial del proceso de despido** (hora exacta de bloqueo)
- RF-36: Notificaciones automáticas del proceso

---

## 👥 Roles y Permisos

### Administrador
- Acceso completo a todas las áreas
- No tiene redirección específica (va a `/kanban/`)

### RRHH
- Iniciar todos los procesos
- Confirmar cierre manual de término de contrato
- Configurar plazos de tareas
- Ver alertas de contratos por vencer
- Dashboard con carga de trabajo por área

### TI
- Creación de cuentas y accesos
- **Bloqueo urgente de accesos** (despido)
- Inventario de equipos TI
- Tablero kanban de tareas

### Prevención de Riesgos
- Exámenes preocupacionales
- EPP e inducción
- Inventario de EPP
- Certificaciones por vencer

### Logística
- **Gestión de devoluciones** (término de contrato)
- **Gestión de recuperaciones** (despido)
- Inventario completo de activos
- Subida de evidencia fotográfica

### Finanzas
- Coordinación de finiquitos
- Vista de procesos de término y despido
- Tablero kanban de tareas

### Jefatura
- Iniciar procesos (igual que RRHH)
- Ver nómina de su CeCo
- Ver tablero de su CeCo
- Recibir alertas de contratos por vencer

---

## 🗄️ Base de Datos

### Modelos Principales

- **User** - Usuarios del sistema (extiende AbstractUser)
- **Role** - Roles (RRHH, TI, Prevención, Logística, Finanzas, Jefatura, Administrador)
- **Worker** - Trabajadores
- **Process** - Procesos (Contratación, Cambio CeCo, Término, Despido)
- **Task** - Tareas dentro de procesos
- **Asset** - Activos (EPP, Equipos TI, etc.)
- **AssetAssignment** - Asignaciones de activos a trabajadores
- **CostCenter** - Centros de costo
- **Notification** - Notificaciones del sistema
- **AuditLog** - Bitácora de auditoría
- **TaskDeadlineConfig** - Configuración de plazos de tareas

---

## 📞 Soporte

Para reportar problemas o solicitar funcionalidades adicionales, contactar al equipo de desarrollo.

---

## 📄 Licencia

Propiedad de Sourcing SPA. Todos los derechos reservados.

---

**Última actualización:** Mayo 2026  
**Versión:** 1.0.0
