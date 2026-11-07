# Pruebas automatizadas

MiGaraje incorpora pruebas automatizadas para verificar el funcionamiento de sus tres microservicios backend: `vehicles-service`, `maintenance-service` y `maintenance-planning-service`.

Las pruebas se implementan con **pytest**, utilizando **FastAPI TestClient** para comprobar las API y bases de datos **SQLite independientes** para evitar modificar los datos de desarrollo o producción.

## 1. Estructura de las pruebas

Cada microservicio dispone de un directorio `tests/` con los siguientes tipos de pruebas:

| Microservicio | Archivos |
|---|---|
| `vehicles-service` | `test_vehicles.py`, `test_migrations.py` |
| `maintenance-service` | `test_maintenance.py`, `test_migrations.py`, `test_vehicles_client.py` |
| `maintenance-planning-service` | `test_planning.py`, `test_migrations.py`, `test_vehicles_client.py` |

Las pruebas comprueban principalmente:

- **Operaciones CRUD:** creación, consulta, actualización y eliminación de vehículos, mantenimientos, reglas y tareas.
- **Validaciones:** campos obligatorios, valores inválidos y restricciones de los datos.
- **Gestión de errores:** recursos inexistentes, referencias incorrectas y servicios externos no disponibles.
- **Health checks:** disponibilidad de los endpoints de salud y comprobación de la conexión con la base de datos.
- **Migraciones:** inicialización de bases de datos nuevas y comprobación de las tablas y revisiones de Alembic.
- **Comunicación entre microservicios:** comportamiento de los clientes HTTP que consultan la existencia de vehículos en `vehicles-service`.

## 2. Aislamiento de las pruebas

Las pruebas de las API utilizan una base de datos SQLite en memoria, independiente de las bases de datos PostgreSQL utilizadas por los servicios.

Las pruebas de migraciones crean una base de datos SQLite temporal mediante `pytest` y ejecutan las migraciones de Alembic sobre ella.

Además, las pruebas de los clientes HTTP simulan las respuestas del servicio de vehículos, por lo que no necesitan que los demás microservicios estén ejecutándose.

De este modo, las pruebas pueden ejecutarse de forma independiente y reproducible, sin utilizar credenciales ni modificar datos de producción.

## 3. Instalación de dependencias

Cada microservicio dispone de un archivo `requirements-dev.txt` que incluye las dependencias de producción y las herramientas necesarias para ejecutar las pruebas.

Desde la raíz del proyecto, ejecutar:

```bash
pip install -r services/vehicles-service/requirements-dev.txt
```

Para trabajar con otro microservicio, se puede instalar su correspondiente archivo de dependencias de desarrollo.

## 4. Ejecución de las pruebas

Los tests se pueden ejecutar de forma independiente desde el directorio de cada microservicio:

**Vehicles Service**

```bash
cd services/vehicles-service
python -m pytest -v
```

**Maintenance Service**

```bash
cd services/maintenance-service
python -m pytest -v
```

**Maintenance Planning Service**

```bash
cd services/maintenance-planning-service
python -m pytest -v
```

Para ejecutar todos los tests desde la raíz del proyecto en PowerShell:

```powershell
$services = @(
    "vehicles-service",
    "maintenance-service",
    "maintenance-planning-service"
)

foreach ($service in $services) {
    Write-Host "`nEjecutando tests de $service..." -ForegroundColor Cyan

    Push-Location "services/$service"

    try {
        python -m pytest -v

        if ($LASTEXITCODE -ne 0) {
            throw "Han fallado los tests de $service."
        }
    }
    finally {
        Pop-Location
    }
}
```

Si alguna prueba falla, el comando devuelve un código de salida distinto de cero.

## 5. Integración continua (CI)

El proyecto utiliza **GitHub Actions** para ejecutar automáticamente las pruebas de los tres microservicios.

El workflow se encuentra en:

```text
.github/workflows/ci.yml
```

Se ejecuta cuando se realiza un `push` a la rama `main`, se crea o actualiza un `pull request` dirigido a `main`, o se inicia manualmente mediante `workflow_dispatch`.

La ejecución utiliza una matriz de servicios, de manera que cada microservicio se prueba en un trabajo independiente.

El workflow configura Python 3.12, instala las dependencias de desarrollo y ejecuta:

```bash
python -m pytest -v
```

Si alguna prueba falla, el trabajo correspondiente de GitHub Actions se marca como fallido.

## 6. Consideraciones

Las pruebas automatizadas permiten comprobar el comportamiento de cada microservicio y detectar regresiones durante el desarrollo.

Las pruebas de los clientes HTTP verifican el tratamiento de las respuestas y errores de comunicación simulados. No sustituyen a una prueba de extremo a extremo con todos los microservicios desplegados y comunicándose entre sí.