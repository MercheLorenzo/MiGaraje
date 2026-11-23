# MiGaraje — Tu garaje digital

**Gestión de vehículos, historial de mantenimientos, planificación, recordatorios y análisis de gastos.**

**Autora:** Mercedes Lorenzo Aragón  
**Proyecto académico:** Cloud Computing: Fundamentos e Infraestructuras · Máster Universitario en Ingeniería Informática · Universidad de Granada (2026–2027).

> Esta versión amplía los tres microservicios originales del proyecto y sustituye la página estática de acceso a Swagger por una aplicación web interactiva. La [documentación original del Hito 1](docs/hito1readme.md) se conserva sin modificaciones.

## ¿Qué problema resuelve?

La información de un vehículo suele estar repartida entre facturas, anotaciones y recordatorios. MiGaraje la reúne en un espacio personal: cuándo se cambió el aceite, qué producto se utilizó, cuánto costó una intervención y cuándo toca la siguiente revisión. Permite gestionar varios vehículos y comparar sus gastos.

## Funciones disponibles

| Módulo | Funcionalidades implementadas |
|---|---|
| **Cuentas y perfil** | Registro, inicio de sesión, edición del nombre, cambio de contraseña con invalidación de sesiones anteriores, cierre de sesión, datos separados por cuenta. |
| **Mi garaje** | Crear, consultar, editar, buscar y eliminar vehículos; marca, modelo, año, tipo, matrícula, combustible, fecha de matriculación, kilometraje, apodo y notas. |
| **Historial** | Crear, consultar, filtrar, editar y borrar intervenciones; fecha, kilómetros, categoría, descripción, taller, productos, pieza, costes de piezas/mano de obra y coste total. |
| **Reglas periódicas** | Crear, editar y eliminar reglas con intervalos en días, meses o km; generar la siguiente tarea calculada y evitar duplicados activos. |
| **Tareas** | Crear tareas manuales o generadas por regla, editarlas, completarlas y eliminarlas; vencimientos por fecha o kilometraje; actualización de la regla al completar una tarea vinculada. |
| **Calendario** | Vista mensual de tareas pendientes con fecha, navegación entre meses y exportación manual a `.ics`. |
| **Estadísticas** | Resumen de gastos, número de intervenciones, coste medio, desglose por categoría, evolución mensual y comparativa entre vehículos, con filtro por año/vehículo. |
| **Notificaciones** | Alertas internas próximas y vencidas, marcarlas como leídas, preferencias de 90/30/7/1 días y envío por correo *opcional* con SMTP. Escaneo periódico mientras el servidor permanece activo. |
| **Exportaciones** | Historial de gastos a CSV, información del garaje a JSON y eventos del calendario a ICS. |

Las indicaciones de mantenimiento se configuran por el usuario y **no sustituyen las recomendaciones del fabricante ni una inspección profesional**.

## Arquitectura

Conserva la separación del proyecto original: los servicios de vehículos, intervenciones y planificación siguen teniendo sus propias API REST y bases de datos lógicas. Se han incorporado tres servicios:

| Componente | Puerto interno | Responsabilidad |
|---|---:|---|
| `vehicles-service` | 8000 | CRUD de vehículos |
| `maintenance-service` | 8001 | Historial y costes |
| `maintenance-planning-service` | 8002 | Reglas, tareas y cálculo de vencimientos |
| `statistics-service` **(nuevo)** | 8003 | Agregaciones por REST, sin leer directamente bases ajenas |
| `notifications-service` **(nuevo)** | 8004 | Avisos persistentes, preferencias, escaneo periódico, SMTP opcional |
| `gateway-service` **(nuevo)** | 8090 | Registro/login, JWT, perfil, asociación usuario↔vehículo y acceso autorizado a las APIs |
| `frontend` | 8080 | Desarrollo: Node.js y live-server |
| `frontend-production` | 8081 | Web estática servida por Nginx con proxy `/api/` |
| `db` | 5432 | PostgreSQL 17 con cinco bases de datos lógicas |

**Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL 17, HTTPX, JWT y `hashlib.scrypt`; HTML/CSS/JavaScript sin framework ni compilación; Nginx, Node.js y Docker Compose. Cada servicio mantiene carpetas `app/api`, `app/services`, `app/models`, `app/clients`/`repositories` y `tests` cuando corresponden.

```text
Navegador (localhost:8081)
     |
   Nginx  -- /api/* --> API Gateway (JWT + permisos)
                               |
            +------------------+-------------------+
            |                  |                   |
         Vehículos        Mantenimientos      Planificación
            |                  |                   |
            +------------------+-----------+-------+
                                       Estadísticas
                                       Notificaciones

      PostgreSQL: vehículos | mantenimiento | planificación
                  gateway | notificaciones
```

Las API de negocio comprueban una **clave interna** adicional y solo publican puertos en `127.0.0.1` para facilitar pruebas locales. El navegador accede a ellas **únicamente a través del Gateway**. Las contraseñas se almacenan mediante scrypt con sal aleatoria y los tokens de sesión caducan tras ocho horas. Para exponer MiGaraje a Internet hacen falta medidas adicionales (HTTPS, endurecimiento y limitación de peticiones).

## Cómo arrancar la aplicación (Windows / PowerShell)

**Requisitos:** Docker Desktop con Docker Compose v2, contenedores Linux, puertos locales `8080`, `8081`, `8090`, `8000–8002` y `5432` disponibles.

**1. Descomprime el ZIP y entra en la carpeta `MiGaraje`** (la que contiene `compose.yaml`).

**2. Crea tu configuración privada:**

```powershell
Copy-Item .env.example .env
notepad .env
```

Si ya tenías `.env`, **no lo sobrescribas**: conserva la contraseña existente y añade las nuevas variables mostradas en `.env.example` (ver [migración de una instalación anterior](docs/INSTALACION_Y_MIGRACION.md)).

**3. Edita `.env`:** reemplaza `change_me_locally` por **la misma contraseña** en `POSTGRES_PASSWORD` y las **cinco** URL de bases de datos (además de la URL heredada `DATABASE_URL`, si la conservas). Sustituye `JWT_SECRET` e `INTERNAL_API_KEY` por **dos cadenas largas, distintas y aleatorias**. Puedes generarlas con Python:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Ejecuta ese comando **dos veces**. No publiques `.env` en GitHub. Para iniciar sin correo electrónico, deja vacías las variables SMTP.

**4. Construye e inicia los contenedores:**

```powershell
docker compose config
docker compose up -d --build
docker compose ps
```

**5. Abre la aplicación:**

- **Web recomendada:** http://localhost:8081
- Web en modo desarrollo: http://localhost:8080
- Documentación del Gateway: http://localhost:8090/docs (las operaciones de usuario necesitan un token JWT)

En la web, elige **Crear cuenta**. Después, registra tu primer vehículo y añade un mantenimiento. Puedes crear reglas y pulsar **Generar tarea** para obtener el siguiente vencimiento.

**6. Consultar logs y parar sin borrar datos:**

```powershell
docker compose logs -f gateway-service
docker compose logs -f notifications-service
docker compose down
```

**No ejecutes `docker compose down -v`**, ya que eliminaría el volumen de PostgreSQL y sus datos.

La guía completa y la recuperación de vehículos preexistentes están en **[INSTALACION_Y_MIGRACION.md](docs/INSTALACION_Y_MIGRACION.md)**.

## Desarrollo y pruebas

Los tres servicios originales conservan sus tests. Los nuevos incluyen tests de autenticación, propiedad de vehículos, cálculo de estadísticas y deduplicación de avisos.

```powershell
# Por ejemplo, dentro de services/gateway-service:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest -q
```

En las verificaciones realizadas para esta entrega, **las pruebas automatizadas de los seis servicios han pasado y también una prueba de integración HTTP entre los seis procesos, usando SQLite local**. Las cinco migraciones se ejecutaron correctamente contra SQLite de prueba. **No se ha ejecutado Docker Compose con PostgreSQL en este entorno**, por lo que ese arranque debe comprobarse en el ordenador de destino.

El workflow de GitHub Actions amplía sus matrices de pruebas e imágenes para los nuevos servicios; Ruff y su formato quedan temporalmente en modo *informativo*, mientras se normaliza el estilo de las nuevas incorporaciones.

## Avisos por correo

Los avisos **dentro de la aplicación no requieren SMTP**. El correo está desactivado por defecto. Para habilitarlo, configura `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` y activa **Recibir correos** en **Notificaciones → Preferencias**. El servicio utiliza STARTTLS en el puerto configurado y no envía correo cuando no existe una configuración válida.

## Alcance y limitaciones de esta versión

- Los gastos se calculan **solo** a partir de las intervenciones registradas: no estiman combustible, seguro, impuestos ni depreciación.
- `parts_cost` y `labor_cost` se guardan como campos opcionales; el total `cost` sigue siendo la referencia económica para estadísticas.
- Las reglas se configuran y **la primera tarea se genera desde el botón «Generar tarea»**. Las tareas vinculadas generan la siguiente tarea cuando se completan; las reglas no crean por sí mismas una tarea hasta que se solicita su primera generación.
- Los avisos de fecha reconocen hitos de 90/30/7/1 días; los de kilometraje se activan a menos de 1000 km, al llegar o al superar el umbral, según los kilómetros almacenados. No se estima automáticamente el kilometraje futuro.
- No hay subida de facturas, fotografías ni integración automática con Google Calendar: el JSON, CSV e ICS son exportaciones locales; **no sustituyen una copia de seguridad completa de PostgreSQL**.
- El borrado de un vehículo elimina sus registros dependientes mediante varias API; no existe transacción distribuida entre microservicios. Es recomendable hacer copia de seguridad antes de eliminar información importante.
- El envío programado solo funciona mientras el contenedor de notificaciones esté ejecutándose. Los avisos pueden regenerarse manualmente con **Comprobar avisos**; se evita repetir el mismo aviso para la misma tarea y plazo.
- Esta es una aplicación académica preparada para desarrollo local. **No la publiques en Internet sin revisar antes la configuración de seguridad, HTTPS y protección frente a abuso**.

## Documentación

- [Hito 1 original](docs/hito1readme.md) (se conserva).
- [Instalación y migración](docs/INSTALACION_Y_MIGRACION.md) — Docker, `.env` y datos anteriores.
- [Funcionalidades y decisiones técnicas añadidas](docs/NUEVAS_FUNCIONALIDADES.md).
- [Inventario completo de archivos nuevos y modificados](docs/INVENTARIO_CAMBIOS.md).
- [Guía de pruebas del proyecto original](docs/testing.md) y documentación `docs/` previa.

**Repositorio:** https://github.com/MercheLorenzo/MiGaraje

© 2026 Mercedes Lorenzo Aragón. Proyecto académico. El repositorio no incluye credenciales privadas ni datos de usuarios.
