# Dockerización y optimización de MiGaraje

## 1. Objetivo

MiGaraje utiliza Docker para empaquetar y ejecutar sus microservicios backend en entornos reproducibles. Cada microservicio dispone de su propio `Dockerfile`, lo que permite construir su imagen de forma independiente y mantener separadas sus dependencias y responsabilidades.

El frontend también dispone de un Dockerfile multi-stage con dos objetivos: desarrollo y producción. De esta manera, se utilizan herramientas adecuadas para cada entorno sin incorporar las herramientas de desarrollo a la imagen final de producción.

Como parte de la optimización de las imágenes, se han aplicado estrategias de construcción multi-stage, separación de dependencias y código, y ejecución con usuarios sin privilegios en los microservicios backend.

Docker Compose se utiliza para coordinar los contenedores, configurar sus variables de entorno, publicar los puertos y establecer las dependencias entre servicios.

## 2. Imagen base de los microservicios backend

Los tres microservicios utilizan `python:3.12-slim` como imagen base.

Se ha elegido esta variante porque proporciona el intérprete de Python necesario para ejecutar las aplicaciones FastAPI sin incluir todos los componentes de una imagen completa de Python. Esto permite reducir los componentes innecesarios y mantener una imagen relativamente ligera.

Además, utilizar la misma versión principal y secundaria de Python en los tres servicios favorece la consistencia del entorno de ejecución.

Los microservicios son:

- `vehicles-service`
- `maintenance-service`
- `maintenance-planning-service`

## 3. Construcción multi-stage de los microservicios backend

Los Dockerfiles utilizan dos etapas principales:

- **`builder`:** instala las dependencias especificadas en `requirements.txt` en un directorio separado.
- **`production`:** parte de una imagen base limpia e incorpora las dependencias instaladas y los archivos necesarios para ejecutar el microservicio.

En el caso de `maintenance-planning-service`, también se copian los archivos de configuración y migraciones de Alembic que necesita la aplicación.

Esta estrategia evita trasladar a la imagen final todo el entorno utilizado durante la preparación de las dependencias y permite distinguir entre la construcción y la ejecución de la aplicación.

## 4. Optimización de la caché de Docker

En los microservicios backend, la instalación de dependencias está separada de la copia del código fuente.

Primero se copia `requirements.txt` y se instalan las dependencias. Posteriormente, se copia el código de la aplicación.

De esta manera, cuando cambia el código pero no las dependencias, Docker puede reutilizar la capa correspondiente a su instalación, evitando repetir ese paso innecesariamente.

Además, las dependencias de ejecución se mantienen en `requirements.txt`, mientras que las dependencias necesarias para las pruebas y el desarrollo se especifican en `requirements-dev.txt`.

Esta separación permite distinguir las bibliotecas necesarias para ejecutar los servicios de aquellas utilizadas durante el desarrollo y las pruebas.

## 5. Seguridad: usuario sin privilegios

Las imágenes de producción de los microservicios crean un usuario y un grupo del sistema denominados `app`. Las aplicaciones se ejecutan mediante la instrucción `USER app`, en lugar de hacerlo como usuario `root`.

Esta decisión aplica el principio de mínimo privilegio y reduce el impacto potencial de una vulnerabilidad en la aplicación.

Los archivos de la aplicación se copian con los permisos y la propiedad correspondientes para que el usuario pueda acceder a ellos durante la ejecución.

## 6. Puertos y comando de inicio del backend

Cada microservicio expone el puerto correspondiente a su aplicación:

| Microservicio | Puerto |
|---|---:|
| `vehicles-service` | 8000 |
| `maintenance-service` | 8001 |
| `maintenance-planning-service` | 8002 |

Los servicios se inician mediante Uvicorn, utilizando `app.main:app` como referencia a la aplicación ASGI y escuchando en `0.0.0.0` para aceptar conexiones desde el entorno de contenedores.

La configuración de publicación de puertos y las variables de entorno se gestionan desde Docker Compose.

## 7. Dockerización del frontend

El frontend de MiGaraje se encuentra en el directorio `frontend/` y actualmente está compuesto por:

- `index.html`: página principal de la aplicación.
- `css/style.css`: hoja de estilos.
- `MiGaraje.png`: logotipo de la aplicación.

Se ha creado un Dockerfile multi-stage que permite construir imágenes independientes para desarrollo y producción.

Ambas etapas sirven el mismo contenido web, pero utilizan servidores y configuraciones diferentes según el objetivo de ejecución.

### 7.1. Etapa de desarrollo

La etapa `development` utiliza `node:22-alpine` e instala `live-server`, un servidor estático que permite visualizar los cambios realizados en los archivos del frontend.

Docker Compose monta el directorio local `frontend/` como volumen dentro del contenedor. De esta manera, los cambios en el HTML, CSS y las imágenes pueden reflejarse en el navegador sin reconstruir la imagen, siempre que el servidor detecte dichos cambios.

La aplicación se publica en el puerto `8080` del equipo.

Para construir y arrancar el frontend de desarrollo:

```powershell
docker compose build frontend
docker compose up -d frontend
```

Acceso a la aplicación:

- Landing page: http://localhost:8080

Para consultar los registros del contenedor:

```powershell
docker compose logs frontend
```

Este entorno está pensado para facilitar la edición y validación de la página durante el desarrollo.

### 7.2. Etapa de producción

La etapa `production` utiliza `nginx:alpine`, un servidor web ligero diseñado para servir los archivos estáticos del frontend.

La imagen final incorpora los archivos necesarios para ejecutar la página, sin incluir Node.js ni `live-server`. De esta manera, se evita incluir herramientas de desarrollo que no son necesarias durante la ejecución en producción.

Nginx escucha en el puerto `80` dentro del contenedor, que se publica en el puerto `8081` del equipo mediante Docker Compose.

Para construir y arrancar el frontend de producción:

```powershell
docker compose up -d --build frontend-production
```

Acceso a la aplicación:

- Landing page: http://localhost:8081

Para consultar los registros del contenedor:

```powershell
docker compose logs frontend-production
```

Cuando se modifican los archivos estáticos, es necesario reconstruir la imagen y recrear el contenedor para que producción utilice la versión actualizada.

### 7.3. Ejecución de los dos entornos

Los servicios `frontend` y `frontend-production` están definidos de forma independiente en `compose.yaml`.

Se puede ejecutar únicamente desarrollo:

```powershell
docker compose up -d frontend
```

O únicamente producción:

```powershell
docker compose up -d --build frontend-production
```

También es posible arrancar ambos entornos:

```powershell
docker compose up -d --build frontend frontend-production
```

En este caso, desarrollo estará disponible en el puerto `8080` y producción en el `8081`.

La selección del entorno se realiza mediante el atributo `build.target` de Docker Compose, que indica qué etapa del Dockerfile debe utilizarse para construir cada imagen.

## 8. Independencia del frontend y acceso a las API

El frontend se ejecuta en su propio contenedor y puede servir la página estática sin que sea necesario ejecutar los microservicios backend.

Los tres microservicios mantienen sus puertos publicados para permitir el acceso a la documentación interactiva de sus API mediante Swagger:

| Microservicio | URL de Swagger |
|---|---|
| Vehículos | http://localhost:8000/docs |
| Mantenimiento | http://localhost:8001/docs |
| Planificación del mantenimiento | http://localhost:8002/docs |

Estas direcciones permiten acceder desde el navegador a la documentación de cada API.

La accesibilidad de Swagger no implica que las llamadas HTTP realizadas desde JavaScript estén configuradas automáticamente. Cuando se incorporen peticiones desde el frontend, será necesario utilizar las URL adecuadas y configurar CORS en los servicios cuando corresponda.

La independencia del frontend permite desarrollar y servir la interfaz por separado, mientras que cada microservicio conserva sus propias responsabilidades y dependencias.

## 9. Validación

Se han realizado las siguientes comprobaciones en el entorno local:

- Construcción y ejecución de los tres microservicios mediante Docker Compose.
- Comprobación de los endpoints de salud de los microservicios.
- Ejecución satisfactoria de las pruebas automatizadas de `vehicles-service`, con 17 tests superados.
- Construcción de las imágenes del frontend para desarrollo y producción.
- Arranque del frontend de desarrollo y acceso a la página principal mediante el puerto `8080`.
- Arranque del frontend de producción y acceso a la página principal mediante el puerto `8081`.
- Comprobación de la carga de la hoja de estilos y del logotipo `MiGaraje.png`.
- Verificación del acceso a la documentación Swagger de los tres microservicios.

Estas comprobaciones permiten validar la construcción de las imágenes y el funcionamiento básico de los servicios en el entorno local.

## 10. Decisiones adoptadas

Las principales decisiones de optimización y diseño son:

- Utilizar `python:3.12-slim` como imagen base de los microservicios backend.
- Separar la instalación de dependencias y la copia del código fuente.
- Utilizar una construcción multi-stage para distinguir la preparación de dependencias y la ejecución de los microservicios.
- Ejecutar las aplicaciones backend con un usuario sin privilegios.
- Mantener un Dockerfile independiente por microservicio.
- Separar las dependencias de ejecución y las de desarrollo mediante `requirements.txt` y `requirements-dev.txt`.
- Utilizar `node:22-alpine` y `live-server` para el entorno de desarrollo del frontend.
- Utilizar `nginx:alpine` para servir los archivos estáticos en producción.
- Mantener objetivos de construcción independientes para desarrollo y producción.
- Utilizar Docker Compose para coordinar los servicios, publicar los puertos y configurar las dependencias entre contenedores.
- Mantener el frontend independiente de los microservicios backend.
- Conservar PostgreSQL en un volumen persistente gestionado por Docker Compose.