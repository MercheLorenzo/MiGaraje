# Vehicles Service

Microservicio de gestión de vehículos de **MiGaraje**, una aplicación cloud-native destinada a facilitar el registro y la gestión de vehículos personales, así como el seguimiento de su mantenimiento.

## Índice

- [Descripción](#descripción)
- [Funcionalidades](#funcionalidades)
- [Tecnologías utilizadas](#tecnologías-utilizadas)
- [Arquitectura y responsabilidades](#arquitectura-y-responsabilidades)
- [Ejecución local](#ejecución-local)
- [Ejecución con Docker](#ejecución-con-docker)
- [Acceso a la API](#acceso-a-la-api)
- [Endpoints](#endpoints)
- [Base de datos y migraciones](#base-de-datos-y-migraciones)
- [Comprobaciones de salud](#comprobaciones-de-salud)
- [Pruebas automatizadas](#pruebas-automatizadas)

## Descripción

`vehicles-service` es un microservicio desarrollado con FastAPI que se encarga de gestionar los vehículos registrados en MiGaraje.

Proporciona una API REST para realizar operaciones sobre los vehículos y persiste su información en una base de datos PostgreSQL. Otros microservicios pueden utilizar esta API para consultar la información necesaria sin acceder directamente a la base de datos de vehículos.

## Funcionalidades

- Registrar nuevos vehículos.
- Consultar los vehículos registrados.
- Consultar un vehículo por su identificador.
- Modificar los datos de un vehículo.
- Eliminar un vehículo.
- Validar los datos recibidos antes de persistirlos.
- Comprobar la disponibilidad del servicio y su conexión con la base de datos.

Entre las validaciones contempladas se encuentran la matrícula, el año del vehículo y el kilometraje, así como la prevención de matrículas duplicadas.

## Tecnologías utilizadas

| Tecnología | Finalidad |
|---|---|
| Python | Lenguaje de programación. |
| FastAPI | Desarrollo de la API REST. |
| Pydantic | Validación de datos. |
| SQLAlchemy | Acceso y persistencia de datos mediante ORM. |
| PostgreSQL | Base de datos relacional. |
| Alembic | Gestión versionada de migraciones de la base de datos. |
| Pytest | Ejecución de pruebas automatizadas. |
| Docker | Empaquetado y ejecución del microservicio en un contenedor. |

## Arquitectura y responsabilidades

Este microservicio mantiene la responsabilidad de gestionar los datos de los vehículos. Expone sus operaciones mediante una API REST y utiliza SQLAlchemy para interactuar con PostgreSQL.

La aplicación se organiza en capas para separar las responsabilidades:

- **API y rutas:** recepción de peticiones HTTP y devolución de respuestas.
- **Servicios:** implementación de la lógica de negocio.
- **Modelos y esquemas:** representación de las entidades y validación de los datos.
- **Persistencia:** conexión e interacción con la base de datos.

La separación en capas facilita el mantenimiento, las pruebas y la evolución independiente del servicio.

## Ejecución local

Para ejecutar el microservicio fuera de Docker, es necesario disponer de Python, instalar las dependencias y configurar la conexión a PostgreSQL.

Desde el directorio del servicio:

```bash
cd services/vehicles-service
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

Configurar la variable de entorno `DATABASE_URL` para que apunte a la base de datos de vehículos. La base de datos debe existir y tener aplicadas las migraciones correspondientes.

Una vez preparada la base de datos, iniciar el servidor:

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará disponible en `http://localhost:8000`.

> **Nota:** la opción `--reload` está destinada al desarrollo local, no a un despliegue de producción.

## Ejecución con Docker

MiGaraje utiliza Docker Compose para coordinar sus servicios y la infraestructura necesaria.

Desde el directorio raíz del proyecto:

```bash
docker compose up -d --build
```

Para consultar el estado de los contenedores:

```bash
docker compose ps
```

Para consultar los logs de este microservicio:

```bash
docker compose logs -f vehicles-service
```

Para detener los servicios:

```bash
docker compose stop
```

No se recomienda eliminar volúmenes de datos al detener o reconstruir los contenedores.

## Acceso a la API

Con el servicio ejecutándose y el puerto publicado en la configuración de Docker Compose, están disponibles las siguientes direcciones:

| Recurso | URL | Descripción |
|---|---|---|
| API | `http://localhost:8000` | Dirección base del servicio. |
| Swagger UI | `http://localhost:8000/docs` | Documentación interactiva para explorar y probar la API. |
| OpenAPI | `http://localhost:8000/openapi.json` | Especificación OpenAPI generada por FastAPI. |
| Salud | `http://localhost:8000/health` | Comprobación básica del servicio. |
| Disponibilidad del proceso | `http://localhost:8000/health/live` | Comprueba que el servicio está vivo. |
| Disponibilidad de la aplicación | `http://localhost:8000/health/ready` | Comprueba que la base de datos es accesible. |

## Endpoints

La API permite realizar las siguientes operaciones sobre los vehículos:

| Método HTTP | Ruta | Descripción |
|---|---|---|
| `POST` | `/vehicles` | Registrar un vehículo. |
| `GET` | `/vehicles` | Consultar los vehículos registrados. |
| `GET` | `/vehicles/{vehicle_id}` | Consultar un vehículo por su identificador. |
| `PUT` | `/vehicles/{vehicle_id}` | Actualizar un vehículo. |
| `DELETE` | `/vehicles/{vehicle_id}` | Eliminar un vehículo. |

Las rutas anteriores describen las operaciones de la API; los parámetros, los códigos de respuesta y los esquemas concretos pueden consultarse en `/docs`.

## Base de datos y migraciones

Este microservicio utiliza PostgreSQL para almacenar los vehículos. La configuración de conexión se realiza mediante la variable de entorno `DATABASE_URL`.

Este microservicio utiliza [Alembic](https://alembic.sqlalchemy.org/) para gestionar los cambios en el esquema de la base de datos y mantener un historial de las migraciones aplicadas.

Alembic permite versionar los cambios del esquema de la base de datos y aplicar las migraciones de forma controlada.

### Aplicación de migraciones en un entorno nuevo

Para inicializar la base de datos en un entorno nuevo, sigue estos pasos:

1. Configurar la variable de entorno `DATABASE_URL` en el archivo `.env` del servicio, indicando la URL de conexión a la base de datos correspondiente.

2. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Aplicar las migraciones:

   ```bash
   python -m alembic upgrade head
   ```

Este comando debe ejecutarse antes de iniciar el microservicio por primera vez. Alembic creará las tablas e índices definidos en el historial de migraciones.

### Generación de nuevas migraciones

Cuando se modifiquen los modelos de SQLAlchemy y sea necesario actualizar el esquema:

1. Modificar los modelos de SQLAlchemy correspondientes.

2. Generar una migración:

   ```bash
   python -m alembic revision --autogenerate -m "descripcion_del_cambio"
   ```

3. Revisar el archivo generado en `alembic/versions/` y corregirlo manualmente si fuera necesario.

4. Aplicar la migración:

   ```bash
   python -m alembic upgrade head
   ```

### Consulta del estado de las migraciones

Para consultar la revisión actualmente aplicada en la base de datos:

```bash
python -m alembic current
```

Para consultar el historial de migraciones disponibles:

```bash
python -m alembic history
```

**Importante:** Antes de aplicar una migración, es necesario revisar su contenido. Se recomienda realizar una copia de seguridad de los datos antes de efectuar cambios en el esquema de una base de datos existente. Las migraciones que ya se hayan aplicado en entornos compartidos no deben modificarse; cualquier cambio posterior debe introducirse mediante una nueva migración.

## Comprobaciones de salud

El microservicio dispone de tres endpoints para comprobar su estado:

- `/health`: comprobación básica de que el servicio responde.
- `/health/live`: comprueba que el proceso está vivo.
- `/health/ready`: comprueba que el servicio puede acceder a la base de datos.

El endpoint de disponibilidad devuelve un estado satisfactorio cuando la conexión a la base de datos funciona. Si no puede acceder a ella, responde con un error HTTP `503 Service Unavailable`.

Estas comprobaciones pueden utilizarse para supervisar el estado del servicio y facilitar la detección de problemas operativos.

## Pruebas automatizadas

Las pruebas se ejecutan mediante Pytest. Incluyen comprobaciones de las operaciones CRUD, validaciones de datos, gestión de recursos inexistentes, comprobaciones de salud y pruebas de las migraciones sobre una base de datos SQLite temporal.

Para ejecutar la suite de pruebas desde el directorio del servicio:

```bash
python -m pytest -v
```

Las pruebas de migraciones verifican que una base de datos nueva puede inicializarse mediante Alembic sin depender de la base de datos de desarrollo.

El servicio cuenta con **17 pruebas automatizadas que pasan correctamente** en la última ejecución documentada.