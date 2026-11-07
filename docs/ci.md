# Integración continua (CI)

## 1. Introducción

MiGaraje utiliza **GitHub Actions** para automatizar la integración continua (*Continuous Integration*, CI). El objetivo es comprobar que los cambios introducidos en el repositorio mantienen la calidad del código, superan las pruebas automatizadas y permiten construir y publicar correctamente las imágenes Docker de los distintos componentes de la aplicación.

El workflow se encuentra en `.github/workflows/ci.yml` y se denomina `MiGaraje CI`.

Además de las comprobaciones de calidad y funcionamiento, el pipeline permite publicar las imágenes Docker de producción en **GitHub Container Registry (GHCR)**, facilitando su distribución y posterior despliegue sin necesidad de construirlas localmente.

## 2. Activación del workflow

El workflow se ejecuta automáticamente cuando se produce alguno de estos eventos:

- **Push a `main`**: comprueba los cambios enviados a la rama principal.
- **Pull request hacia `main`**: valida los cambios antes de integrarlos en la rama principal.
- **Ejecución manual**: permite iniciar el workflow desde la pestaña *Actions* de GitHub mediante `workflow_dispatch`.

Se ha establecido el permiso global `contents: read`, limitando los permisos generales del workflow a la lectura del repositorio. El job encargado de publicar las imágenes dispone adicionalmente del permiso `packages: write`, necesario para subirlas a GHCR.

La publicación está restringida a los cambios enviados a `main` y a las ejecuciones manuales realizadas desde esa misma rama. Los eventos de Pull Request no publican imágenes.

## 3. Jobs del workflow

El pipeline está organizado en cinco jobs principales, que permiten validar el código, comprobar la construcción de las imágenes, verificar la comunicación entre microservicios y publicar las imágenes de producción.

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

### 3.5. Publicación de imágenes en GitHub Container Registry

El job `publish-images` se encarga de publicar las cuatro imágenes Docker de producción en **GitHub Container Registry (GHCR)**.

Este job depende de que hayan finalizado correctamente los cuatro jobs anteriores:

- `test`
- `lint-dockerfiles`
- `build-images`
- `integration-tests`

De esta forma, las imágenes únicamente se publican cuando todas las validaciones han terminado correctamente.

Para realizar la publicación se utilizan las siguientes herramientas y acciones:

1. **Docker Buildx** (`docker/setup-buildx-action`): configura el entorno de construcción de imágenes.
2. **Autenticación en GHCR** (`docker/login-action`): permite iniciar sesión en el registro utilizando el usuario que ejecuta GitHub Actions y el secreto automático `GITHUB_TOKEN`.
3. **Construcción y publicación** (`docker/build-push-action`): construye las imágenes utilizando el target `production` y las envía al registro mediante `push: true`.

El job dispone de los permisos `contents: read` y `packages: write`. Este último permite publicar paquetes en GitHub Container Registry sin necesidad de utilizar un token personal.

Las imágenes se publican con el nombre del repositorio y una etiqueta basada en el identificador completo del commit (`github.sha`). De esta manera, cada versión publicada queda asociada al cambio que la ha generado.

El formato de las etiquetas es:

`sha-<identificador-del-commit>`

Por ejemplo:

`sha-eb36fe05e5f5d1fae6f92f3dd556b8c6629afd80`

Las cuatro imágenes publicadas son:

| Componente | Imagen en GHCR |
|---|---|
| Vehicles Service | `ghcr.io/merchelorenzo/migaraje-vehicles-service` |
| Maintenance Service | `ghcr.io/merchelorenzo/migaraje-maintenance-service` |
| Maintenance Planning Service | `ghcr.io/merchelorenzo/migaraje-maintenance-planning-service` |
| Frontend | `ghcr.io/merchelorenzo/migaraje-frontend` |

Las imágenes pueden consultarse desde la sección **Packages** del perfil de GitHub y descargarse directamente mediante Docker.

Por ejemplo, para descargar una versión concreta:

```bash
docker pull ghcr.io/merchelorenzo/migaraje-vehicles-service:sha-eb36fe05e5f5d1fae6f92f3dd556b8c6629afd80
```

La misma operación puede realizarse con las imágenes de los otros tres componentes, sustituyendo el nombre de la imagen.

Esta publicación permite distribuir las imágenes de producción y utilizarlas en otros entornos sin necesidad de disponer del código fuente ni construirlas localmente.

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
| Docker Buildx | Construcción de imágenes Docker. |
| Docker Login Action | Autenticación en GitHub Container Registry. |
| Docker Build Push Action | Construcción y publicación de imágenes en GHCR. |
| GitHub Container Registry (GHCR) | Almacenamiento y distribución de las imágenes Docker. |

## 5. Consulta de los resultados

Los resultados de las ejecuciones pueden consultarse en GitHub, accediendo al repositorio y seleccionando la pestaña **Actions**.

Cada ejecución muestra el estado de los distintos jobs:

- **Success**: todas las comprobaciones del job han terminado correctamente.
- **Failure**: alguna comprobación ha fallado. Se pueden consultar los logs para identificar el problema.

El job `publish-images` permite comprobar el resultado de la publicación de cada una de las cuatro imágenes.

Además, los paquetes publicados pueden consultarse desde la sección **Packages** del perfil de GitHub:

[https://github.com/MercheLorenzo?tab=packages](https://github.com/MercheLorenzo?tab=packages)

Desde esta sección es posible acceder a cada imagen y consultar sus versiones y etiquetas disponibles.

La descarga de las imágenes también permite verificar que se encuentran disponibles en el registro y que pueden recuperarse mediante Docker.

## 6. Conclusión

La incorporación de este pipeline de integración continua permite automatizar las principales comprobaciones de calidad y funcionamiento de MiGaraje. De esta forma, cada cambio puede validarse de manera reproducible, reduciendo la posibilidad de introducir errores y facilitando el mantenimiento de una arquitectura basada en microservicios y contenedores.

Además, la integración con GitHub Container Registry amplía el alcance del pipeline, ya que no solo comprueba que las imágenes Docker pueden construirse, sino que también permite publicar y distribuir las versiones de producción de los cuatro componentes de la aplicación.

Así, MiGaraje dispone de un proceso automatizado que abarca desde la validación del código hasta la publicación de las imágenes necesarias para su posterior despliegue.