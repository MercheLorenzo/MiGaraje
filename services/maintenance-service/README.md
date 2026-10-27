# Maintenance Service

Microservicio de gestión de mantenimientos y reparaciones de **MiGaraje**, una aplicación cloud-native destinada a registrar las intervenciones realizadas en los vehículos y facilitar el seguimiento de sus costes e historial.

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

`maintenance-service` es un microservicio desarrollado con FastAPI que gestiona las intervenciones de mantenimiento y reparación asociadas a los vehículos registrados en MiGaraje.

Permite registrar y consultar intervenciones, almacenar información como la fecha, el kilometraje, el coste y los productos utilizados, y mantener un historial de las operaciones realizadas.

El servicio persiste sus propios datos en PostgreSQL y se comunica con `vehicles-service` cuando necesita comprobar que el vehículo al que se asocia una intervención existe.

## Funcionalidades

- Registrar intervenciones de mantenimiento o reparación.
- Consultar las intervenciones registradas.
- Consultar una intervención por su identificador.
- Consultar el historial de intervenciones de un vehículo.
- Modificar los datos de una intervención.
- Eliminar una intervención.
- Almacenar información sobre kilometraje, coste y productos utilizados.
- Validar los datos antes de persistirlos.
- Verificar la existencia del vehículo asociado mediante `vehicles-service`.
- Comprobar la disponibilidad del servicio y su conexión con la base de datos.

Las validaciones contemplan, entre otros aspectos, la ausencia de productos cuando estos son obligatorios según el modelo y la prohibición de valores negativos para el kilometraje y el coste.

## Tecnologías utilizadas

| Tecnología | Finalidad |
|---|---|
| Python | Lenguaje de programación. |
| FastAPI | Desarrollo de la API REST. |
| Pydantic | Validación de datos. |
| SQLAlchemy | Acceso y persistencia de datos mediante ORM. |
| PostgreSQL | Base de datos relacional. |
| Alembic | Gestión versionada de migraciones de la base de datos. |
| HTTP y JSON | Comunicación entre microservicios mediante API REST. |
| Pytest | Ejecución de pruebas automatizadas. |
| Docker | Empaquetado y ejecución del microservicio en un contenedor. |

## Arquitectura y responsabilidades

Este microservicio es responsable de gestionar los datos de mantenimiento y reparación. Expone una API REST para las operaciones relacionadas con las intervenciones y utiliza SQLAlchemy para interactuar con PostgreSQL.

La aplicación separa las responsabilidades en capas:

- **API y rutas:** recepción de peticiones HTTP y devolución de respuestas.
- **Servicios:** implementación de la lógica de negocio.
- **Modelos y esquemas:** representación de las intervenciones y validación de datos.
- **Persistencia:** conexión e interacción con la base de datos.

Esta organización facilita el mantenimiento y permite evolucionar el servicio sin concentrar toda la lógica en los endpoints.

## Comunicación con otros microservicios

`maintenance-service` depende de `vehicles-service` para verificar la existencia de un vehículo antes de asociarle una intervención.

La comunicación se realiza mediante peticiones HTTP a la API REST de vehículos, sin consultar directamente sus tablas de PostgreSQL.

La URL base del servicio de vehículos se configura mediante la variable de entorno correspondiente definida en el proyecto. En el entorno local, si se utilizan los puertos predeterminados, la API de vehículos está disponible en `http://localhost:8000`.

En Docker Compose, los microservicios deben comunicarse utilizando el nombre del servicio y el puerto interno configurado en la red de Docker, no necesariamente la dirección `localhost`.

Si el servicio de vehículos no está disponible, `maintenance-service` contempla el error y puede responder con `503 Service Unavailable`. Si el vehículo no existe, devuelve un error de validación correspondiente.

## Ejecución local

Para ejecutar el microservicio fuera de Docker, es necesario disponer de Python, instalar las dependencias y configurar la conexión a PostgreSQL.

Desde el directorio del servicio:

```bash
cd services/maintenance-service
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

Configurar `DATABASE_URL` para que apunte a la base de datos de mantenimientos y configurar la URL de `vehicles-service` según el nombre de la variable utilizada en el código.

La base de datos debe existir y tener aplicadas las migraciones correspondientes. Una vez preparada la configuración, iniciar el servidor:

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

El servidor estará disponible en `http://localhost:8001`.

> **Nota:** la opción `--reload` está destinada al desarrollo local, no a un despliegue de producción.

## Ejecución con Docker

MiGaraje utiliza Docker Compose para coordinar los microservicios y la infraestructura necesaria.

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
docker compose logs -f maintenance-service
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
| API | `http://localhost:8001` | Dirección base del servicio. |
| Swagger UI | `http://localhost:8001/docs` | Documentación interactiva para explorar y probar la API. |
| OpenAPI | `http://localhost:8001/openapi.json` | Especificación OpenAPI generada por FastAPI. |
| Salud | `http://localhost:8001/health` | Comprobación básica del servicio. |
| Disponibilidad del proceso | `http://localhost:8001/health/live` | Comprueba que el servicio está vivo. |
| Disponibilidad de la aplicación | `http://localhost:8001/health/ready` | Comprueba que la base de datos es accesible. |

## Endpoints

La API permite realizar las siguientes operaciones sobre las intervenciones:

| Método HTTP | Ruta | Operación |
|---|---|---|
| `POST` | `/maintenances` | Registrar una intervención de mantenimiento. |
| `GET` | `/maintenances` | Consultar las intervenciones registradas. |
| `GET` | `/maintenances/{maintenance_id}` | Consultar una intervención por su identificador. |
| `GET` | `/maintenances/vehicle/{vehicle_id}` | Consultar las intervenciones asociadas a un vehículo. |
| `PUT` | `/maintenances/{maintenance_id}` | Actualizar una intervención. |
| `DELETE` | `/maintenances/{maintenance_id}` | Eliminar una intervención. |

Para consultar las rutas exactas, sus parámetros y los códigos de respuesta, accede a `http://localhost:8001/docs`. Esta documentación interactiva refleja los endpoints registrados por FastAPI.

## Base de datos y migraciones

Este microservicio utiliza PostgreSQL para almacenar las intervenciones de mantenimiento. La conexión se configura mediante la variable de entorno `DATABASE_URL`.

Alembic permite gestionar los cambios del esquema de la base de datos de manera versionada.

### Aplicación de migraciones en un entorno nuevo

1. Configurar `DATABASE_URL` para apuntar a la base de datos de mantenimientos.
2. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Aplicar las migraciones:

   ```bash
   python -m alembic upgrade head
   ```

Este paso debe realizarse antes de iniciar el microservicio en un entorno nuevo.

### Generación de nuevas migraciones

Cuando se modifiquen los modelos de SQLAlchemy y sea necesario actualizar el esquema:

1. Modificar los modelos correspondientes.
2. Generar una migración:

   ```bash
   python -m alembic revision --autogenerate -m "descripcion_del_cambio"
   ```

3. Revisar el archivo generado en `alembic/versions/` y corregirlo manualmente si fuera necesario.
4. Aplicar la migración:

   ```bash
   python -m alembic upgrade head
   ```

### Consulta del estado

Consultar la revisión aplicada:

```bash
python -m alembic current
```

Consultar el historial de migraciones:

```bash
python -m alembic history
```

**Importante:** las migraciones generadas automáticamente deben revisarse antes de aplicarse. Se recomienda realizar una copia de seguridad antes de modificar el esquema de una base de datos con datos importantes. Las migraciones que ya se hayan aplicado en entornos compartidos no deben editarse; los cambios posteriores deben introducirse mediante nuevas migraciones.

## Comprobaciones de salud

El microservicio dispone de tres endpoints para comprobar su estado:

- `/health`: comprobación básica de que el servicio responde.
- `/health/live`: comprueba que el proceso está vivo.
- `/health/ready`: comprueba que el servicio puede acceder a la base de datos.

El endpoint de disponibilidad devuelve un estado satisfactorio cuando la conexión a la base de datos funciona. Si no puede acceder a ella, responde con un error HTTP `503 Service Unavailable`.

Estas comprobaciones permiten detectar problemas de disponibilidad y facilitan la supervisión operativa del servicio.

## Pruebas automatizadas

Las pruebas se ejecutan mediante Pytest. Incluyen operaciones CRUD, validaciones de datos, consulta del historial por vehículo, comprobación de la existencia del vehículo en `vehicles-service`, gestión de errores de comunicación, comprobaciones de salud y pruebas de migraciones sobre una base de datos SQLite temporal.

Para ejecutar la suite de pruebas desde el directorio del servicio:

```bash
python -m pytest -v
```

Las pruebas de migraciones verifican que una base de datos nueva puede inicializarse mediante Alembic sin modificar la base de datos de desarrollo.

El servicio cuenta con **21 pruebas automatizadas que pasan correctamente** en la última ejecución documentada.
