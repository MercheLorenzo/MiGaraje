# Gateway Service — cuentas y acceso autorizado

El punto de entrada del navegador a los servicios de MiGaraje. Se ha añadido al proyecto de microservicios existente sin sustituir ninguna de las tres API originales.

## Responsabilidades

- Alta de cuenta y login con correo y contraseña (`POST /api/auth/register` y `/api/auth/login`).
- Perfil (`GET/PUT /api/auth/me`) y cambio de contraseña (`POST /api/auth/change-password`).
- Sesiones JWT HS256 con caducidad de 8 horas y contraseñas derivadas con scrypt y sal aleatoria.
- Tabla `vehicle_owners`: cada cuenta solamente puede consultar y modificar sus vehículos y los recursos vinculados.
- Operaciones de vehículos, mantenimientos, reglas y tareas desde `/api/vehicles`, `/api/maintenances`, `/api/rules`, `/api/tasks`.
- Estadísticas `/api/statistics/{summary|monthly|categories|comparison}` y notificaciones `/api/notifications`.
- Endpoint interno de cuentas `/internal/users`, protegido por `X-Internal-Key`, para el escáner de recordatorios.

Los endpoints están documentados en `http://localhost:8090/docs` al ejecutar Docker Compose. El navegador no debe consultar directamente los servicios de negocio.

## Configuración

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | Base PostgreSQL propia (`migaraje_gateway`) en Docker, SQLite para pruebas locales. |
| `JWT_SECRET` | Secreto aleatorio, distinto de la clave interna; obligatorio cambiarlo antes de usar datos reales. |
| `INTERNAL_API_KEY` | Clave compartida para comunicación entre microservicios. |
| `VEHICLES_SERVICE_URL` | Dirección HTTP interna de vehículos. |
| `MAINTENANCE_SERVICE_URL` | Dirección HTTP interna de mantenimientos. |
| `PLANNING_SERVICE_URL` | Dirección HTTP interna de planificación. |
| `STATISTICS_SERVICE_URL` | Dirección HTTP interna de estadísticas. |
| `NOTIFICATIONS_SERVICE_URL` | Dirección HTTP interna de notificaciones. |

El arranque recomendado es desde la raíz: `docker compose up -d --build`. Las migraciones se aplican en el contenedor `gateway-migrations` antes de iniciar el Gateway.

## Datos de versiones anteriores

Los vehículos de bases preexistentes no se asignan automáticamente a la primera persona que inicia sesión. Sigue `../../docs/INSTALACION_Y_MIGRACION.md` para crear la cuenta y ejecutar el comando administrativo `app.tools.claim_legacy_vehicles`, que permite asociarlos explícitamente. No ejecutes el comando sin verificar su correo y los identificadores de vehículos.

## Pruebas

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

**Seguridad:** pensado para ejecución local. Si se publica en Internet es necesario añadir TLS/HTTPS, limitación de solicitudes, revisión de configuración de CORS, gestión robusta de secretos y pruebas adicionales de seguridad.
