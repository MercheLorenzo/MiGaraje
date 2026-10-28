## Comprobaciones de salud (Health Checks)

MiGaraje incorpora comprobaciones de salud para verificar que los servicios están funcionando correctamente y que las bases de datos están disponibles. Estas comprobaciones permiten a Docker identificar los contenedores que se encuentran operativos y detectar posibles problemas durante el arranque.

### Endpoints de salud del backend

Los tres microservicios backend exponen los siguientes endpoints:

| Endpoint | Descripción |
|---|---|
| `/health` | Comprueba que el endpoint de salud responde correctamente. |
| `/health/live` | Comprueba que el servicio está activo y responde a las peticiones. |
| `/health/ready` | Comprueba que el servicio puede atender peticiones y que existe conexión con su base de datos. |

Los endpoints están disponibles en las siguientes direcciones:

| Servicio | URL |
|---|---|
| Vehicles Service | `http://localhost:8000/health` |
| Maintenance Service | `http://localhost:8001/health` |
| Maintenance Planning Service | `http://localhost:8002/health` |

Para comprobar la disponibilidad y conectividad con la base de datos, se puede acceder al endpoint `/health/ready` de cada servicio:

- Vehicles Service: `http://localhost:8000/health/ready`
- Maintenance Service: `http://localhost:8001/health/ready`
- Maintenance Planning Service: `http://localhost:8002/health/ready`

Cuando el servicio y su base de datos están disponibles, el endpoint devuelve el código HTTP `200 OK`. Si no puede establecer la conexión con la base de datos, devuelve `503 Service Unavailable`.

### Health checks de Docker

Se han configurado comprobaciones de salud en Docker Compose para los siguientes componentes:

- **PostgreSQL:** comprueba la disponibilidad de la base de datos mediante `pg_isready`.
- **Microservicios backend:** consultan sus respectivos endpoints `/health/ready` para verificar tanto la respuesta del servicio como la conexión con su base de datos.
- **Frontend de desarrollo:** comprueba que el servidor web responde en el puerto `8080`.
- **Frontend de producción:** comprueba que Nginx responde correctamente en el puerto `80` del contenedor, publicado en el puerto `8081` del equipo anfitrión.

Las comprobaciones tienen configurados intervalos, tiempos de espera, número de reintentos y, cuando corresponde, un periodo inicial para permitir que los servicios terminen de arrancar.

Además, las dependencias de Docker Compose utilizan condiciones como `service_healthy` y `service_completed_successfully` para controlar el orden de inicio de los servicios y asegurar que las migraciones de base de datos finalicen correctamente antes de iniciar los servicios dependientes.

### Verificación

Para validar la configuración y reconstruir los contenedores, ejecutar desde la raíz del proyecto:

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

Para consultar el estado de salud de los contenedores:

```powershell
docker inspect --format '{{.Name}}: {{if .State.Health}}{{.State.Health.Status}}{{else}}no healthcheck{{end}}' migaraje-frontend migaraje-frontend-production migaraje-vehicles-service migaraje-maintenance-service migaraje-maintenance-planning-service migaraje-postgres
```

Para consultar los endpoints del backend desde PowerShell:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/health/ready
Invoke-WebRequest -UseBasicParsing http://localhost:8001/health/ready
Invoke-WebRequest -UseBasicParsing http://localhost:8002/health/ready
```

Para comprobar los frontends:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8080/
Invoke-WebRequest -UseBasicParsing http://localhost:8081/
```

La verificación realizada confirmó que los endpoints del backend respondían con `200 OK`, que ambos frontends respondían correctamente en sus páginas principales y que Docker mostraba los seis contenedores principales como `healthy`.

**Nota:** los health checks permiten detectar problemas de disponibilidad, pero no reinician automáticamente un contenedor solo por encontrarse en estado `unhealthy`. La política de reinicio configurada y las condiciones de dependencia de Docker Compose tienen un comportamiento distinto.
