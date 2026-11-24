# MiGaraje · Panel de administración (solo lectura)

## Objetivo y alcance

Esta fase añade una **segunda experiencia de usuario** a MiGaraje sin alterar el acceso de los usuarios normales. Una cuenta ordinaria sigue viendo exclusivamente sus vehículos y mantenimientos. Una cuenta con rol `admin` ve además la opción **Administración → Panel global**, donde puede consultar:

- Número total de usuarios, vehículos y mantenimientos.
- Gastos globales y coste medio, con filtro por año (o todos los años).
- Evolución mensual y gastos por categoría.
- Listado de todos los usuarios: nombre, correo, rol, cantidad de vehículos, mantenimientos y gastos históricos.
- Listado de todos los vehículos: marca, modelo, matrícula, kilometraje, propietario, cantidad de intervenciones y gasto histórico.
- Listado de todos los mantenimientos: fecha, vehículo, tipo, descripción, propietario y coste.
- Filtros por usuario, vehículo, año y búsqueda textual.

**El panel administrativo es de solo lectura.** No existen rutas `POST`, `PUT`, `PATCH` o `DELETE` bajo `/api/admin`; un administrador puede modificar exclusivamente sus propios registros mediante las rutas ordinarias, igual que cualquier usuario. El navegador no determina los permisos: el Gateway verifica el rol en cada petición a `/api/admin`.

Los vehículos anteriores que todavía no estén asignados a una cuenta aparecen como «Sin asignar». La sección de estadísticas siempre muestra los totales globales; los filtros de usuario/vehículo se aplican a los listados. El filtro de año afecta a estadísticas y a la lista de mantenimientos, mientras que los gastos históricos de usuarios y vehículos abarcan todo el periodo.

## Requisitos

- Versión de MiGaraje que ya incluye Gateway, seis microservicios, frontend y Docker Compose.
- Una cuenta registrada **previamente** con contraseña propia.
- Acceso a la terminal del ordenador que ejecuta Docker.
- Una copia de seguridad de PostgreSQL antes de aplicar migraciones, especialmente si contiene datos reales.

## Instalación paso a paso

**1. Trabaja desde la nueva rama**, después de haber fusionado la fase anterior:

```powershell
git switch main
git pull --ff-only origin main
git switch -c feature/panel-administracion
git push -u origin feature/panel-administracion
```

**2. Copia los archivos del ZIP de actualización** sobre el repositorio. Conserva `.git`, `.env`, volúmenes y carpetas de datos. No ejecutes `docker compose down -v`.

**3. Reconstruye el Gateway y el frontend:**

```powershell
docker compose up -d --build gateway-service frontend frontend-production
docker compose ps -a
docker compose logs --tail=80 gateway-migrations
```

La migración nueva `002_admin_role.py` añade `users.role` con valor `user` por defecto, **sin borrar las cuentas existentes**. Los contenedores de migración deben terminar con `Exited (0)`.

**4. Registra tu cuenta normal** en `http://localhost:8081` (si ya existe, no hace falta registrarla de nuevo). Después, desde PowerShell en la carpeta MiGaraje:

```powershell
docker compose exec gateway-service python -m app.scripts.set_admin --email TU_CORREO@EJEMPLO.COM
```

La utilidad debe indicar que el rol se ha actualizado. Cierra sesión y vuelve a iniciar sesión. Esto es necesario porque, por seguridad, los tokens anteriores se revocan al modificar el rol.

**5. Abre `http://localhost:8081`**. La opción «Administración → Panel global» aparecerá en el menú. También puedes probar en Swagger (`http://localhost:8090/docs`), utilizando **Authorize** con el token de la nueva sesión.

**6. Para retirar los permisos de administrador:**

```powershell
docker compose exec gateway-service python -m app.scripts.set_admin --email TU_CORREO@EJEMPLO.COM --role user
```

Cierra sesión y vuelve a entrar tras retirar el rol.

> No existe una cuenta administradora predeterminada ni una contraseña de administrador publicada. El registro público siempre crea cuentas `user`, aunque se intente enviar el campo `role` en el JSON.

## Rutas nuevas de Swagger

Todas requieren `Authorization: Bearer <token>` con una cuenta cuyo rol sea `admin`:

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/admin/overview?year=2026` | Totales globales, categorías y meses; `year` opcional |
| GET | `/api/admin/users` | Usuarios y métricas históricas por persona |
| GET | `/api/admin/vehicles?user_id=2` | Todos los vehículos o los de un usuario |
| GET | `/api/admin/maintenances?user_id=2&vehicle_id=5&year=2026` | Historial global, filtros opcionales |

Una sesión normal devuelve `403 Forbidden`; una petición sin sesión devuelve `401 Unauthorized`. Los hashes de las contraseñas no se incluyen en las respuestas. Las APIs internas de vehículos y mantenimientos siguen protegidas por la clave interna: el Gateway consulta esos servicios, no sus tablas SQL.

## Guion breve para demostración de correcto funcionamiento

1. Registrar «Persona A» y «Persona B» con datos ficticios.
2. Con «Persona A», crear dos vehículos y registrar dos mantenimientos. Con «Persona B», crear otro vehículo y un mantenimiento.
3. Mostrar que «Persona A» no ve el vehículo de «Persona B», ni en el frontend ni llamando a `/api/vehicles` con su token.
4. Promover una tercera cuenta de demostración a `admin` desde Docker y volver a iniciar sesión con ella.
5. Mostrar el panel global: tres vehículos, tres intervenciones, sumas de costes y listados con propietario.
6. Filtrar por usuario, año y vehículo. Comprobar la misma información con los endpoints `/api/admin/...` de Swagger.
7. Mostrar que el panel **no tiene botones de edición ni borrado**; intentar llamar a `/api/admin/overview` con un token normal y comprobar el código `403`.

## Validación automatizada

```powershell
cd services/gateway-service
python -m pytest -q
```

GitHub Actions ejecuta los tests de los seis servicios y, en su entorno de PostgreSQL **desechable**, el script `python -m scripts.e2e_admin`, que cubre registro, promoción, revocación de JWT antiguos, acceso global, seguridad entre usuarios y limpieza de vehículos temporales. Este script **no se debe ejecutar contra tu base de datos real**, ya que crea cuentas de prueba y el mecanismo de limpieza solo elimina los vehículos, no las cuentas.

## Limitaciones y consideraciones

- Este panel está orientado a instalaciones pequeñas y demostración. Para grandes cantidades de datos sería conveniente incorporar paginación, búsquedas en servidor y auditoría de accesos administrativos.
- Utiliza datos ficticios en la demostración. En una instalación real habría que informar a los usuarios de quién accede a sus registros y con qué finalidad; revisar los requisitos aplicables de privacidad y protección de datos.
- Las métricas globales se obtienen consultando los servicios REST existentes, sin compartir tablas de datos entre microservicios.
- Un administrador no puede cambiar roles desde el navegador; solo desde una terminal autorizada en el servidor.
- `main` debe permanecer estable: trabaja en `feature/panel-administracion` hasta que Docker, las pruebas manuales y GitHub Actions pasen correctamente.
