# Notifications Service — avisos y recordatorios

Microservicio FastAPI independiente con tablas `notification_preferences` y `notifications` y su propia base de datos lógica `migaraje_notifications`.

## Funcionalidades

- Genera avisos basados en fechas próximas/vencidas y kilometraje registrado, con hitos de **90, 30, 7 y 1 día** configurables y avisos por proximidad a un umbral de km.
- Evita duplicados para un mismo usuario, tarea, vencimiento y plazo.
- Conserva el estado leído/no leído, la configuración del usuario y el resultado del envío de correo opcional.
- Ejecuta un escaneo periódico (por defecto cada 3600 segundos) mientras el servicio esté activo; permite invocar escaneos manuales desde el Gateway.
- Soporta servidor SMTP con STARTTLS si se configura y el usuario activa el envío.

## Endpoints internos

| Método | Ruta | Función |
|---|---|---|
| GET | `/notifications/{user_id}` | Listar los últimos avisos. |
| GET/PUT | `/notifications/{user_id}/preferences` | Consultar y actualizar configuración. |
| POST | `/notifications/{user_id}/scan` | Solicitar comprobación de vencimientos. |
| PATCH | `/notifications/{user_id}/{notification_id}/read` | Marcar aviso como leído. |
| POST | `/notifications/{user_id}/test` | Enviar correo de prueba con limitación de frecuencia. |
| GET | `/health/live`, `/health/ready` | Comprobar salud. |

`INTERNAL_API_KEY` protege sus rutas de negocio y el Gateway es el responsable de la identidad y el permiso sobre el usuario concreto.

## Variables de entorno

`DATABASE_URL`, `INTERNAL_API_KEY`, `PLANNING_SERVICE_URL`, `VEHICLES_SERVICE_URL`, `GATEWAY_SERVICE_URL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `NOTIFICATION_INTERVAL_SECONDS`. No hace falta SMTP para avisos visibles dentro de la web. El escáner inicia con el servicio y las migraciones se ejecutan en `notifications-migrations`.

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

**Límites:** no hay predicción automática de kilómetros, notificaciones push ni envío de correos cuando no se configura SMTP. Para alojarlo en Internet hacen falta controles de seguridad y monitorización adicionales.
