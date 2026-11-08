# Integración del frontend en el entorno MiGaraje

## 1. Introducción

El frontend de MiGaraje está integrado en el entorno local de Docker Compose junto con los tres microservicios backend y PostgreSQL.

La aplicación dispone de dos configuraciones:

- **Desarrollo:** utiliza Node.js y `live-server`, permitiendo detectar cambios en los archivos del frontend.
- **Producción:** utiliza Nginx para servir los archivos estáticos de la aplicación.

Ambas configuraciones permiten acceder a la misma landing page y conectarse con los servicios backend.

## 2. Configuración de Docker Compose

El frontend se define en `compose.yaml` mediante dos servicios:

| Servicio | Imagen base | Puerto local | Puerto del contenedor |
|---|---|---:|---:|
| `frontend` | Node.js 22 Alpine | 8080 | 8080 |
| `frontend-production` | Nginx Alpine | 8081 | 80 |

El servicio de desarrollo monta el directorio `frontend/` como volumen, de forma que los cambios realizados en los archivos se reflejan durante la ejecución.

La versión de producción copia los archivos estáticos necesarios (`index.html`, CSS y logotipo) a la carpeta pública de Nginx.

Ambos servicios cuentan con healthchecks para comprobar que el servidor web está disponible.

## 3. Acceso a la aplicación

Una vez iniciado el entorno, se puede acceder a las siguientes direcciones desde el navegador:

| Componente | URL |
|---|---|
| Frontend (desarrollo) | http://localhost:8080 |
| Frontend (producción) | http://localhost:8081 |
| Vehicles Service | http://localhost:8000/docs |
| Maintenance Service | http://localhost:8001/docs |
| Maintenance Planning Service | http://localhost:8002/docs |

Las interfaces Swagger permiten consultar y probar los endpoints disponibles en cada microservicio.

## 4. Arranque del entorno completo

Desde el directorio raíz del proyecto, ejecutar:

```bash
docker compose up -d --build
```

Este comando construye las imágenes necesarias y arranca los servicios definidos en `compose.yaml`.

Para comprobar el estado de los contenedores:

```bash
docker compose ps
```

Los servicios backend y frontend deben aparecer en estado `healthy` cuando sus respectivos healthchecks hayan finalizado correctamente.

Para consultar los registros de ejecución:

```bash
docker compose logs -f
```

## 5. Comunicación entre frontend y backend

Los tres microservicios backend están publicados en puertos accesibles desde el navegador:

- Vehicles Service: `http://localhost:8000`
- Maintenance Service: `http://localhost:8001`
- Maintenance Planning Service: `http://localhost:8002`

El frontend incluye enlaces directos a la documentación Swagger de cada servicio.

Para permitir futuras peticiones HTTP desde el navegador, se ha configurado el middleware `CORSMiddleware` de FastAPI en los tres microservicios.

Se autorizan los siguientes orígenes:

- `http://localhost:8080` (desarrollo).
- `http://localhost:8081` (producción).

Esta configuración permite que el navegador acceda a las respuestas de las APIs desde ambos frontends, respetando la política de seguridad CORS.

**Nota:** la interfaz actual proporciona acceso a la documentación de los microservicios mediante enlaces. La implementación de operaciones funcionales desde el frontend mediante llamadas HTTP queda fuera del alcance de esta integración.

## 6. Verificación de la integración

Se han realizado las siguientes comprobaciones:

- Acceso correcto a la landing page desde los puertos 8080 y 8081.
- Carga correcta de los archivos CSS y del logotipo de MiGaraje.
- Acceso a la documentación Swagger de los tres microservicios desde ambos frontends.
- Comprobación de la comunicación HTTP desde el navegador mediante peticiones `fetch()` a los endpoints `/health/ready`.
- Verificación de respuestas HTTP `200 OK` de los tres servicios desde ambos orígenes.
- Confirmación de que los tres servicios devuelven el estado de la base de datos como `ok`.
- Resolución de los errores CORS mediante la configuración de `CORSMiddleware`.

Con estas pruebas se verifica que el frontend está integrado en el entorno Docker Compose y que puede acceder a los tres servicios backend desde el navegador.

## 7. Detención del entorno

Para detener los contenedores sin eliminar los datos persistentes:

```bash
docker compose down
```

Los volúmenes de PostgreSQL se conservan, por lo que los datos almacenados no se eliminan al detener el entorno.