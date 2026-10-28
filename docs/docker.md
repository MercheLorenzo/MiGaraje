# Dockerización y optimización de los microservicios de MiGaraje

## 1. Objetivo

MiGaraje utiliza Docker para empaquetar y ejecutar sus microservicios backend en entornos reproducibles. Cada microservicio dispone de su propio `Dockerfile`, lo que permite construir su imagen de forma independiente y mantener separadas sus dependencias y responsabilidades.

Como parte de la optimización de las imágenes, se han aplicado builds multi-stage, separación de dependencias y código, y ejecución con usuarios sin privilegios.

## 2. Imagen base

Los tres microservicios utilizan `python:3.12-slim` como imagen base.

Se ha elegido esta variante porque proporciona el intérprete de Python necesario para ejecutar las aplicaciones FastAPI sin incluir todos los componentes de una imagen completa de Python. Esto permite reducir los componentes innecesarios y mantener una imagen relativamente ligera.

Además, utilizar la misma versión principal y secundaria de Python en los tres servicios favorece la consistencia del entorno de ejecución.

## 3. Construcción multi-stage

Los Dockerfiles utilizan dos etapas principales:

- **`builder`:** instala las dependencias especificadas en `requirements.txt` en un directorio separado.
- **`production`:** parte de una imagen base limpia e incorpora las dependencias instaladas y los archivos necesarios para ejecutar el microservicio.

En el caso de `maintenance-planning-service`, también se copian los archivos de configuración y migraciones de Alembic que necesita la aplicación.

Esta estrategia evita trasladar a la imagen final todo el entorno utilizado durante la preparación de las dependencias y permite distinguir entre la construcción y la ejecución de la aplicación.

## 4. Optimización de la caché de Docker

La instalación de dependencias está separada de la copia del código fuente.

Primero se copia `requirements.txt` y se instalan las dependencias. Posteriormente, se copia el código de la aplicación.

De esta manera, cuando cambia el código pero no las dependencias, Docker puede reutilizar la capa correspondiente a su instalación, evitando repetir ese paso innecesariamente.

## 5. Seguridad: usuario sin privilegios

Las imágenes de producción crean un usuario y un grupo del sistema denominados `app`. La aplicación se ejecuta mediante la instrucción `USER app`, en lugar de hacerlo como usuario `root`.

Esta decisión aplica el principio de mínimo privilegio y reduce el impacto potencial de una vulnerabilidad en la aplicación.

Los archivos de la aplicación se copian con los permisos y la propiedad correspondientes para que el usuario pueda acceder a ellos durante la ejecución.

## 6. Puertos y comando de inicio

Cada Dockerfile expone el puerto correspondiente a su microservicio:

| Microservicio | Puerto |
|---|---:|
| `vehicles-service` | 8000 |
| `maintenance-service` | 8001 |
| `maintenance-planning-service` | 8002 |

Los servicios se inician mediante Uvicorn, utilizando `app.main:app` como referencia a la aplicación ASGI y escuchando en `0.0.0.0` para aceptar conexiones desde el entorno de contenedores.

La configuración de publicación de puertos y las variables de entorno se gestionan desde Docker Compose.

## 7. Entorno de producción y posible entorno de desarrollo

Actualmente, los Dockerfiles están orientados a la construcción de imágenes de producción mediante la etapa final `production`. No se ha añadido una etapa específica `development` porque no es necesaria para cumplir el objetivo actual de optimizar las imágenes de producción.

Si en el futuro se necesita ejecutar los servicios en contenedores con herramientas de desarrollo, recarga automática o dependencias de pruebas, se podría incorporar una etapa adicional denominada `development`.

Esta etapa podría instalar las dependencias de desarrollo y utilizar una configuración de ejecución apropiada para trabajar con el código fuente. Docker Compose podría seleccionar esa etapa mediante `build.target`.

La etapa de desarrollo sería independiente de la imagen final de producción, que continuaría utilizando únicamente las dependencias y los archivos necesarios para ejecutar la aplicación.

## 8. Validación

Se ha comprobado que los tres microservicios pueden construirse y arrancar mediante Docker Compose. También se han verificado sus endpoints de salud, que responden correctamente.

Además, los tests automatizados de `vehicles-service` han finalizado satisfactoriamente, con 17 tests superados.

Estas comprobaciones permiten validar tanto la construcción de las imágenes como el funcionamiento básico de los servicios en el entorno local.

## 9. Decisiones adoptadas

Las principales decisiones de optimización y seguridad son:

- Utilizar `python:3.12-slim` como imagen base.
- Separar la instalación de dependencias y la copia del código.
- Utilizar una construcción multi-stage con una etapa final `production`.
- Ejecutar las aplicaciones con un usuario sin privilegios.
- Mantener un Dockerfile independiente por microservicio.
- Utilizar Docker Compose para coordinar los servicios y PostgreSQL.
- Dejar la incorporación de una etapa `development` para cuando exista una necesidad concreta de ejecutar herramientas de desarrollo dentro de contenedores.