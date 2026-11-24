# MiGaraje — guía de pruebas de la API REST y Swagger

Esta guía describe la API pública del **Gateway** y cómo usarla con el frontend sin acceder directamente a las bases de datos ni a las API internas.

## Accesos locales

- **Frontend de producción:** http://localhost:8081
- **Frontend de desarrollo:** http://localhost:8080
- **Swagger UI (Gateway):** http://localhost:8090/docs
- **ReDoc:** http://localhost:8090/redoc
- **OpenAPI en JSON:** http://localhost:8090/openapi.json

> En Swagger se utiliza el Gateway, no los puertos internos de los microservicios. Los servicios de vehículos, mantenimiento y planificación utilizan una clave interna: no hay que introducirla en el navegador ni compartirla. El endpoint `/internal/users` es exclusivamente para comunicación interna, por eso no aparece en Swagger.

## Autenticarse en Swagger (imprescindible)

1. Abre `http://localhost:8090/docs`.
2. Expande `POST /api/auth/register` si aún no tienes cuenta, o `POST /api/auth/login` si ya la tienes.
3. Pulsa **Try it out**. Introduce correo y contraseña (mínimo 10 caracteres) y pulsa **Execute**.
4. En la respuesta aparecerá un campo `token`. Copia **solo el valor del token**, sin las comillas.
5. Pulsa el botón **Authorize** arriba a la derecha. En `HTTPBearer` pega el token sin anteponer `Bearer` y confirma.
6. Ya puedes probar cualquier ruta protegida. Si aparece 401, vuelve a iniciar sesión y actualiza la autorización; las sesiones caducan.

**Atención:** Swagger puede ejecutar operaciones reales. `DELETE` elimina registros de la base de datos. Utiliza una cuenta y vehículos de prueba antes de trabajar con datos importantes.

## Catálogo de operaciones

### Auth y perfil

| Método | Ruta | Función |
|---|---|---|
| POST | `/api/auth/register` | Crear cuenta |
| POST | `/api/auth/login` | Iniciar sesión y obtener JWT |
| GET | `/api/auth/me` | Consultar perfil |
| PUT | `/api/auth/me` | Cambiar nombre completo |
| POST | `/api/auth/change-password` | Cambiar contraseña e invalidar tokens anteriores |

### Vehículos

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/vehicles` | Listar mis vehículos |
| POST | `/api/vehicles` | Crear vehículo |
| GET | `/api/vehicles/{vehicle_id}` | Consultar vehículo |
| PUT | `/api/vehicles/{vehicle_id}` | Modificar vehículo |
| DELETE | `/api/vehicles/{vehicle_id}` | Eliminar vehículo y sus registros vinculados |

### Mantenimientos

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/maintenances` | Listar intervenciones; admite `?vehicle_id=1` |
| POST | `/api/maintenances` | Registrar intervención |
| GET | `/api/maintenances/{record_id}` | Consultar intervención |
| PUT | `/api/maintenances/{record_id}` | Editar intervención |
| DELETE | `/api/maintenances/{record_id}` | Eliminar intervención |

### Reglas periódicas

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/rules` | Listar reglas; admite `?vehicle_id=1` |
| POST | `/api/rules` | Crear regla |
| GET | `/api/rules/{record_id}` | Consultar regla |
| PUT | `/api/rules/{record_id}` | Modificar regla |
| DELETE | `/api/rules/{record_id}` | Eliminar regla y sus tareas relacionadas |
| POST | `/api/rules/{rule_id}/generate` | Generar una tarea para el siguiente vencimiento |

### Tareas

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/tasks` | Listar tareas; admite `?vehicle_id=1` y `?status=pending` |
| POST | `/api/tasks` | Crear tarea |
| GET | `/api/tasks/{record_id}` | Consultar tarea |
| PUT | `/api/tasks/{record_id}` | Modificar tarea |
| DELETE | `/api/tasks/{record_id}` | Eliminar tarea |
| PATCH | `/api/tasks/{task_id}/complete` | Marcar tarea como completada |

El parámetro `status` admite `pending`, `upcoming`, `overdue` o `completed`.

### Estadísticas

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/statistics/summary` | Totales, número de intervenciones, coste medio |
| GET | `/api/statistics/monthly` | Gastos y operaciones por mes |
| GET | `/api/statistics/categories` | Desglose por categorías |
| GET | `/api/statistics/comparison` | Comparativa entre vehículos |
| GET | `/api/statistics/vehicles/{vehicle_id}` | Estadísticas detalladas de un vehículo |

Admiten el parámetro opcional `year`, y las cuatro primeras también `vehicle_id`. Solo se devuelven datos de vehículos asociados a la sesión.

### Notificaciones

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/notifications` | Listar avisos |
| POST | `/api/notifications/scan` | Comprobar tareas y crear avisos pendientes |
| GET | `/api/notifications/preferences` | Consultar preferencias |
| PUT | `/api/notifications/preferences` | Modificar preferencias |
| PATCH | `/api/notifications/{notification_id}/read` | Marcar un aviso como leído |
| POST | `/api/notifications/test` | Probar envío SMTP (requiere configuración) |

### Salud

- `GET /health/live` — proceso activo.
- `GET /health/ready` — proceso preparado y base de datos conectada.

## Ejemplos para Swagger

Los campos adicionales están documentados en los esquemas `VehicleIn`, `MaintenanceIn`, `RuleIn`, `TaskIn` y `CompleteTaskIn`. Reemplaza los identificadores por los que devuelve tu base de datos.

### 1. Registrar una cuenta

```json
{
  "full_name": "Persona de prueba",
  "email": "pruebas@example.org",
  "password": "ContrasenaLargaDePrueba123"
}
```

### 2. Crear un coche (`POST /api/vehicles`)

```json
{
  "brand": "Seat",
  "model": "Ibiza",
  "year": 2021,
  "license_plate": "1234ABC",
  "current_mileage": 62000,
  "vehicle_type": "car",
  "fuel_type": "gasoline",
  "registration_date": "2021-05-10",
  "nickname": "Coche diario",
  "notes": "Ejemplo creado desde Swagger"
}
```

### 3. Registrar mantenimiento (`POST /api/maintenances`)

```json
{
  "vehicle_id": 1,
  "maintenance_type": "oil_change",
  "date": "2026-11-20",
  "mileage": 62000,
  "description": "Aceite y filtro",
  "cost": "95.00",
  "workshop": "Taller de pruebas",
  "products_used": "Aceite 5W-30",
  "parts_cost": "65.00",
  "labor_cost": "30.00"
}
```

### 4. Crear regla (`POST /api/rules`)

```json
{
  "vehicle_id": 1,
  "name": "Cambio de aceite anual",
  "maintenance_type": "oil_change",
  "interval_months": 12,
  "interval_kilometers": 15000,
  "last_performed_date": "2026-11-20",
  "last_performed_mileage": 62000,
  "reminder_days_before": 30,
  "is_active": true
}
```

Al menos uno de los campos `interval_days`, `interval_months` o `interval_kilometers` debe ser positivo. Para generar la tarea: `POST /api/rules/{rule_id}/generate`.

### 5. Crear tarea manual (`POST /api/tasks`)

```json
{
  "vehicle_id": 1,
  "name": "Revisar neumáticos",
  "description": "Comprobar presión y dibujo",
  "due_date": "2027-02-01"
}
```

Debe incluirse `due_date` o `due_mileage`. Para completarla:

```json
{
  "completed_date": "2027-02-01",
  "completed_mileage": 65000
}
```

### 6. Configurar recordatorios (`PUT /api/notifications/preferences`)

```json
{
  "email_enabled": false,
  "reminder_offsets_days": [30, 7, 1]
}
```

Deja `email_enabled` en `false` si no has configurado SMTP en tu `.env`.

## Comparar la API con el frontend

1. En **Swagger**, registra un vehículo con `POST /api/vehicles`.
2. Entra en **http://localhost:8081**, inicia sesión con **la misma cuenta** y abre **Mis vehículos**: debe aparecer.
3. Añade desde la web un mantenimiento. Vuelve a Swagger y consulta `GET /api/maintenances`: debe aparecer.
4. Consulta `GET /api/statistics/summary` y contrasta las cifras con **Estadísticas** en el frontend, seleccionando el mismo periodo (el frontend filtra por año).
5. Crea una regla y una tarea desde Swagger, y comprueba **Reglas periódicas**, **Próximas tareas** y **Calendario** en la web.

El frontend y Swagger utilizan **el mismo Gateway**, por lo que comparten registros y autenticación. Swagger no inicia sesión automáticamente cuando lo haces en el frontend: debes autorizarlo por separado con el token JWT.

## Instalar los cambios en tu repositorio

Reemplaza los archivos del ZIP de actualización **conservando `.env`, `.git`, `compose.yaml`, PostgreSQL y tus datos**. Desde la carpeta del proyecto, ejecuta:

```powershell
docker compose up -d --build gateway-service
docker compose ps
```

Vuelve a cargar `http://localhost:8090/docs` (Ctrl + F5). Si aparecen rutas antiguas, confirma que el contenedor Gateway se haya reconstruido con el archivo nuevo y revisa `docker compose logs gateway-service`.

## Errores habituales

| Código | Significado |
|---|---|
| 401 | No se ha enviado un JWT válido o ha caducado. |
| 404 | El recurso no existe o no pertenece a tu cuenta. |
| 409 | Conflicto, por ejemplo matrícula duplicada. |
| 422 | El JSON no cumple el esquema, faltan campos o el dato es inválido. |
| 503 | Una API interna no está disponible o falta SMTP para la prueba de correo. |

Las rutas de la API están descritas en OpenAPI, pero su ejecución real depende del estado de los microservicios y de la base de datos. El cambio de documentación no necesita nuevas migraciones de base de datos.
