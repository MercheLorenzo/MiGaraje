# Maintenance Planning Service

Microservicio de planificación de mantenimientos de **MiGaraje**, una aplicación cloud-native destinada a facilitar la gestión de los vehículos, registrar sus intervenciones y anticipar las tareas de mantenimiento que deben realizarse.

## Índice

- [Descripción](#descripción)
- [Funcionalidades](#funcionalidades)
- [Tecnologías utilizadas](#tecnologías-utilizadas)
- [Arquitectura y responsabilidades](#arquitectura-y-responsabilidades)
- [Comunicación con otros microservicios](#comunicación-con-otros-microservicios)
- [Ejecución local](#ejecución-local)
- [Ejecución con Docker](#ejecución-con-docker)
- [Acceso a la API](#acceso-a-la-api)
- [Endpoints](#endpoints)
- [Base de datos y migraciones](#base-de-datos-y-migraciones)
- [Comprobaciones de salud](#comprobaciones-de-salud)
- [Pruebas automatizadas](#pruebas-automatizadas)

## Descripción

`maintenance-planning-service` es un microservicio desarrollado con FastAPI que gestiona las reglas y las tareas de planificación de mantenimiento de los vehículos registrados en MiGaraje.

Su objetivo es facilitar el seguimiento de los mantenimientos periódicos, teniendo en cuenta criterios como el tiempo transcurrido y el kilometraje. De esta forma, permite definir cuándo corresponde realizar determinadas operaciones y organizar las tareas de mantenimiento asociadas a cada vehículo.

El servicio utiliza PostgreSQL para persistir sus datos y SQLAlchemy para interactuar con la base de datos. Alembic permite gestionar de forma versionada los cambios en el esquema.

## Funcionalidades

- Registrar reglas de mantenimiento para un vehículo.
- Consultar las reglas de mantenimiento registradas.
- Definir intervalos de mantenimiento por días, meses o kilómetros.
- Almacenar información sobre la última realización de un mantenimiento, incluida su fecha y kilometraje.
- Configurar con cuánta antelación se desea recibir un aviso.
- Activar o desactivar reglas de mantenimiento.
- Gestionar tareas de mantenimiento asociadas a las reglas.
- Persistir las reglas y tareas en PostgreSQL.
- Validar los datos antes de almacenarlos.
- Comprobar la disponibilidad del servicio y su conexión con la base de datos.

Las reglas permiten representar operaciones periódicas como el cambio de aceite, la sustitución de filtros o las revisiones del vehículo.

La detección automática de tareas próximas o vencidas y el envío de notificaciones forman parte de la evolución funcional del sistema y deben considerarse implementados únicamente cuando estén desarrollados y probados.

## Tecnologías utilizadas

| Tecnología | Finalidad |
|---|---|
| Python | Lenguaje de programación. |
| FastAPI | Desarrollo de la API REST. |
| Pydantic | Validación de datos de entrada y salida. |
| SQLAlchemy | Acceso y persistencia de datos mediante ORM. |
| PostgreSQL | Base de datos relacional. |
| Alembic | Gestión versionada de migraciones de la base de datos. |
| HTTP y JSON | Comunicación entre microservicios mediante API REST. |
| Pytest | Ejecución de pruebas automatizadas. |
| Docker | Empaquetado y ejecución del microservicio en un contenedor. |
| Docker Compose | Coordinación de los microservicios y la infraestructura local. |

## Arquitectura y responsabilidades

Este microservicio es responsable de gestionar las reglas y las tareas relacionadas con la planificación de los mantenimientos. Expone una API REST para las operaciones disponibles y utiliza SQLAlchemy para interactuar con PostgreSQL.

La aplicación organiza sus responsabilidades en capas:

- **API y rutas:** recepción de peticiones HTTP y devolución de respuestas.
- **Servicios:** implementación de la lógica de negocio.
- **Modelos y esquemas:** representación de las reglas y tareas, y validación de datos.
- **Persistencia:** configuración de la conexión y acceso a la base de datos.

Esta separación facilita el mantenimiento, las pruebas y la evolución independiente del servicio.

### Modelo de datos

El servicio contempla dos entidades principales:

- **MaintenanceRule:** representa una regla de mantenimiento asociada a un vehículo, con información sobre el tipo de operación, sus intervalos, la última realización y la configuración de avisos.
- **MaintenanceTask:** representa una tarea de mantenimiento vinculada a una regla, permitiendo organizar las operaciones que deben realizarse.

Las tareas mantienen una relación con sus reglas de mantenimiento mediante una clave foránea.

## Comunicación con otros microservicios

`maintenance-planning-service` forma parte de la arquitectura de microservicios de MiGaraje y debe coordinarse con los servicios responsables de los vehículos y de las intervenciones realizadas.

- **`vehicles-service`:** gestiona los vehículos registrados y constituye la referencia para asociar las reglas de mantenimiento a un vehículo.
- **`maintenance-service`:** registra las intervenciones y reparaciones realizadas, cuya información puede utilizarse para actualizar los datos de planificación.

La comunicación entre microservicios se realiza mediante interfaces HTTP/REST cuando sea necesaria. Cada servicio mantiene sus propias responsabilidades y no debe acceder directamente a las tablas de la base de datos de otro microservicio.

La URL del servicio de vehículos y las demás conexiones necesarias se configuran mediante variables de entorno. En Docker Compose, los servicios deben comunicarse utilizando los nombres de los servicios y sus puertos internos.

La integración completa entre los tres microservicios debe verificarse mediante pruebas de integración.

## Ejecución local

Para ejecutar el microservicio fuera de Docker es necesario disponer de Python, instalar las dependencias y configurar el acceso a PostgreSQL.

Desde el directorio raíz del proyecto:

```powershell
cd services/maintenance-planning-service
```

Crear y activar un entorno virtual en Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instalar las dependencias:

```powershell
pip install -r requirements.txt
```

Configurar la variable `PLANNING_DATABASE_URL` para que apunte a la base de datos de planificación. La base de datos debe existir y tener aplicadas las migraciones correspondientes.

Aplicar las migraciones:

```powershell
python -m alembic upgrade head
```

Iniciar el servidor:

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

El servicio estará disponible en `http://localhost:8002`.

> **Nota:** la opción `--reload` está destinada al desarrollo local, no a un despliegue de producción.

## Ejecución con Docker

MiGaraje utiliza Docker Compose para coordinar los microservicios y la infraestructura necesaria. La configuración se encuentra en el archivo `compose.yaml`, situado en el directorio raíz del proyecto.

Desde dicho directorio, ejecutar:

```powershell
docker compose -f compose.yaml up -d --build
```

Para consultar el estado de los contenedores:

```powershell
docker compose -f compose.yaml ps
```

Para consultar los logs de este microservicio:

```powershell
docker compose -f compose.yaml logs -f maintenance-planning-service
```

Para reconstruir únicamente la imagen del microservicio después de modificar su código o sus dependencias:

```powershell
docker compose -f compose.yaml up -d --build maintenance-planning-service
```

Para detener los servicios:

```powershell
docker compose -f compose.yaml stop
```

> **Importante:** detener o reconstruir los contenedores no requiere eliminar los volúmenes de PostgreSQL. No se debe utilizar `docker compose down -v` para las operaciones habituales de desarrollo, ya que podría eliminar los datos persistidos.

## Acceso a la API

Con el servicio ejecutándose y el puerto publicado en la configuración de Docker Compose, están disponibles las siguientes direcciones:

| Recurso | URL | Descripción |
|---|---|---|
| API | `http://localhost:8002` | Dirección base del servicio. |
| Swagger UI | `http://localhost:8002/docs` | Documentación interactiva para explorar y probar la API. |
| OpenAPI | `http://localhost:8002/openapi.json` | Especificación OpenAPI generada por FastAPI. |
| Salud | `http://localhost:8002/health` | Comprobación básica del servicio. |
| Disponibilidad del proceso | `http://localhost:8002/health/live` | Comprueba que el servicio está vivo. |
| Disponibilidad de la aplicación | `http://localhost:8002/health/ready` | Comprueba que la base de datos es accesible. |

La documentación de Swagger permite consultar los parámetros, los esquemas de datos y las respuestas de los endpoints disponibles.

## Endpoints

La API proporciona operaciones relacionadas con las reglas y las tareas de mantenimiento.

Entre las operaciones previstas para las reglas se encuentran:

| Método HTTP | Operación |
|---|---|
| `POST` | Crear una regla de mantenimiento. |
| `GET` | Consultar las reglas de mantenimiento. |
| `GET` | Consultar una regla por su identificador. |
| `PUT` | Actualizar una regla de mantenimiento. |
| `DELETE` | Eliminar una regla de mantenimiento. |

El servicio también contempla operaciones sobre las tareas de mantenimiento.

La tabla anterior describe las operaciones CRUD previstas; para conocer las rutas exactas y comprobar cuáles están implementadas actualmente, consulta `http://localhost:8002/docs`. La documentación interactiva de FastAPI refleja los endpoints registrados en la aplicación.

## Base de datos y migraciones

Este microservicio utiliza PostgreSQL para almacenar las reglas y las tareas de planificación. La conexión se configura mediante la variable de entorno `PLANNING_DATABASE_URL`.

Dentro del entorno Docker Compose, la base de datos lógica utilizada por este servicio es `migaraje_planning`.

La infraestructura utiliza una instancia de PostgreSQL con varias bases de datos lógicas para separar los datos de los microservicios. Esta configuración simplifica el entorno de desarrollo sin eliminar la separación de responsabilidades entre los servicios.

### Aplicación de migraciones en un entorno nuevo

1. Configurar `PLANNING_DATABASE_URL`.
2. Crear la base de datos `migaraje_planning` si todavía no existe.
3. Instalar las dependencias:

   ```powershell
   pip install -r requirements.txt
   ```

4. Aplicar las migraciones:

   ```powershell
   python -m alembic upgrade head
   ```

Este paso debe realizarse antes de utilizar el servicio en un entorno nuevo.

Si se utiliza Docker Compose, se puede aplicar la migración mediante:

```powershell
docker compose -f compose.yaml exec maintenance-planning-service python -m alembic upgrade head
```

### Generación de nuevas migraciones

Cuando se modifiquen los modelos de SQLAlchemy y sea necesario actualizar el esquema:

1. Modificar los modelos correspondientes.
2. Generar una migración:

   ```powershell
   python -m alembic revision --autogenerate -m "descripcion_del_cambio"
   ```

3. Revisar el archivo generado en `alembic/versions/` y corregirlo manualmente si fuera necesario.
4. Aplicar la migración:

   ```powershell
   python -m alembic upgrade head
   ```

### Consulta del estado

Consultar la revisión aplicada:

```powershell
python -m alembic current
```

Consultar el historial de migraciones:

```powershell
python -m alembic history
```

**Importante:** las migraciones generadas automáticamente deben revisarse antes de aplicarse. Se recomienda realizar una copia de seguridad antes de modificar el esquema de una base de datos con datos importantes. Las migraciones ya aplicadas en entornos compartidos no deben editarse; los cambios posteriores deben introducirse mediante nuevas migraciones.

## Comprobaciones de salud

El microservicio dispone de tres endpoints para comprobar su estado:

- `/health`: comprobación básica de que el servicio responde.
- `/health/live`: comprueba que el proceso está vivo.
- `/health/ready`: comprueba que el servicio puede acceder a la base de datos.

El endpoint de disponibilidad permite comprobar si la aplicación está preparada para atender peticiones que requieren acceso a PostgreSQL. Si la base de datos no está disponible, debe devolver un error HTTP `503 Service Unavailable`.

Estas comprobaciones facilitan la detección de problemas operativos y pueden utilizarse en la supervisión de los contenedores.

## Pruebas automatizadas

Las pruebas se ejecutan mediante Pytest y permiten comprobar el comportamiento del microservicio de forma automatizada.

La suite de pruebas desarrollada contempla la validación de las operaciones del servicio, los modelos de datos y la lógica relacionada con las reglas y las tareas de mantenimiento.

Para ejecutar las pruebas desde el directorio del microservicio:

```powershell
python -m pytest -v
```

También se pueden ejecutar desde el directorio raíz indicando la ruta del servicio:

```powershell
python -m pytest -v services/maintenance-planning-service/tests
```

Las pruebas de migraciones pueden ejecutarse sobre una base de datos SQLite temporal para verificar que el esquema puede inicializarse mediante Alembic sin modificar la base de datos de desarrollo.

En la última ejecución documentada, el servicio contaba con **36 pruebas automatizadas superadas**. Conviene volver a ejecutar la suite antes de cerrar esta fase para confirmar el estado actual del código.

