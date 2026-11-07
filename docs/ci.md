# Integración continua (CI)

## 1. Introducción

MiGaraje utiliza **GitHub Actions** para automatizar la integración continua (Continuous Integration, CI). El objetivo es comprobar que los cambios introducidos en el repositorio mantienen la calidad del código, superan las pruebas automatizadas y permiten construir correctamente las imágenes Docker de los distintos componentes de la aplicación.

El workflow se encuentra en `.github/workflows/ci.yml` y se denomina `MiGaraje CI`.

## 2. Activación del workflow

El workflow se ejecuta automáticamente cuando se produce alguno de estos eventos:

- **Push a `main`**: comprueba los cambios enviados directamente a la rama principal.
- **Pull request hacia `main`**: valida los cambios antes de integrarlos en la rama principal.
- **Ejecución manual**: permite iniciar el workflow desde la pestaña *Actions* de GitHub mediante `workflow_dispatch`.

Se ha establecido el permiso `contents: read`, limitando los permisos del workflow a la lectura del repositorio.

## 3. Jobs del workflow

El pipeline está organizado en cuatro jobs independientes.

### 3.1. Test de los microservicios

El job `test` utiliza una matriz de ejecución para realizar las comprobaciones de forma independiente en los tres microservicios:

- `vehicles-service`
- `maintenance-service`
- `maintenance-planning-service`

Para cada servicio se realizan las siguientes operaciones:

1. Descargar el código del repositorio.
2. Configurar Python 3.12.
3. Instalar las dependencias de desarrollo definidas en `requirements-dev.txt`.
4. Ejecutar **Ruff** para comprobar la calidad y el estilo del código mediante `ruff check .`.
5. Comprobar el formato del código con `ruff format --check .`.
6. Ejecutar las pruebas automatizadas mediante `python -m pytest -v`.

De esta forma, cada microservicio se valida de manera independiente.

### 3.2. Análisis de los Dockerfiles

El job `lint-dockerfiles` utiliza **Hadolint** para analizar los cuatro Dockerfiles del proyecto:

- `frontend/Dockerfile`
- `services/vehicles-service/Dockerfile`
- `services/maintenance-service/Dockerfile`
- `services/maintenance-planning-service/Dockerfile`

Se establece el nivel `warning` como umbral de fallo (`failure-threshold: warning`), por lo que las advertencias y los errores detectados impiden que la validación termine correctamente.

Esta comprobación permite detectar malas prácticas y posibles problemas en la construcción de las imágenes.

### 3.3. Construcción de imágenes Docker

El job `build-images` comprueba que se pueden construir las imágenes Docker de los cuatro componentes:

- `migaraje-vehicles-service`
- `migaraje-maintenance-service`
- `migaraje-maintenance-planning-service`
- `migaraje-frontend`

Las imágenes se construyen utilizando el target `production` y se etiquetan con el sufijo `:ci`.

Esta fase permite detectar errores en los Dockerfiles, en las dependencias o en el proceso de construcción antes de integrar los cambios.

### 3.4. Pruebas de integración

El job `integration-tests` comprueba el funcionamiento conjunto de los microservicios mediante peticiones HTTP reales.

Para ello, GitHub Actions prepara un entorno temporal con credenciales de prueba y utiliza Docker Compose para levantar PostgreSQL, ejecutar la inicialización de las bases de datos y las migraciones, y arrancar los tres microservicios.

Una vez que los servicios están disponibles, se ejecuta el script `scripts/integration_tests.py`.

Las pruebas comprueban:

- La disponibilidad de los tres microservicios.
- La creación de un vehículo.
- La creación de un mantenimiento asociado a un vehículo existente.
- El rechazo de un mantenimiento cuando el vehículo no existe.
- La creación de una regla de mantenimiento.
- El rechazo de una regla asociada a un vehículo inexistente.
- La creación de una tarea de mantenimiento.
- El rechazo de una tarea asociada a un vehículo inexistente.

Estas pruebas permiten verificar la comunicación real entre servicios, complementando las pruebas unitarias, que utilizan dependencias simuladas (*mocks*).

Si se produce un fallo, se muestran los logs de Docker Compose para facilitar el diagnóstico. Al finalizar, se detienen los servicios del entorno de pruebas.

## 4. Herramientas utilizadas

| Herramienta | Finalidad |
|---|---|
| GitHub Actions | Automatización del pipeline CI. |
| Python 3.12 | Entorno de ejecución de los microservicios y las pruebas. |
| Ruff | Análisis estático y comprobación del formato del código Python. |
| pytest | Ejecución de pruebas automatizadas. |
| Hadolint | Análisis de buenas prácticas en Dockerfiles. |
| Docker | Construcción y ejecución de contenedores. |
| Docker Compose | Orquestación del entorno de integración. |
| PostgreSQL 17 | Base de datos utilizada por los microservicios. |

## 5. Consulta de los resultados

Los resultados de las ejecuciones pueden consultarse en GitHub, accediendo al repositorio y seleccionando la pestaña **Actions**.

Cada ejecución muestra el estado de los distintos jobs:

- **Success**: todas las comprobaciones del job han terminado correctamente.
- **Failure**: alguna comprobación ha fallado. Se pueden consultar los logs para identificar el problema.

El pipeline permite detectar errores de código, problemas en los Dockerfiles, fallos en la construcción de imágenes y problemas de comunicación entre microservicios antes de integrar los cambios en `main`.

## 6. Conclusión

La incorporación de este pipeline de integración continua permite automatizar las principales comprobaciones de calidad y funcionamiento de MiGaraje. De esta forma, cada cambio puede validarse de manera reproducible, reduciendo la posibilidad de introducir errores y facilitando el mantenimiento de una arquitectura basada en microservicios y contenedores.