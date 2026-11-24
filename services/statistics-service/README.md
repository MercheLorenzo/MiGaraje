# Statistics Service — estadísticas de MiGaraje

Servicio independiente FastAPI que consulta los datos de vehículos e intervenciones **a través de sus APIs REST** (HTTPX). No dispone de base de datos propia ni accede directamente a tablas de otros microservicios.

## Endpoints

| Método | Ruta | Resultado |
|---|---|---|
| GET | `/statistics/summary` | Gastos totales, número de intervenciones y coste medio. |
| GET | `/statistics/monthly` | Gastos distribuidos por mes. |
| GET | `/statistics/categories` | Gastos agrupados por tipo de intervención. |
| GET | `/statistics/comparison` | Gastos comparados entre vehículos. |
| GET | `/statistics/vehicles/{vehicle_id}` | Indicadores de un vehículo. |
| GET | `/health/live` y `/health/ready` | Salud del servicio. |

Las consultas agregadas aceptan `vehicle_ids` (identificadores separados por comas) y `year` (año opcional). La comprobación de propiedad la realiza el **Gateway**, no este servicio. Los importes se agregan con `Decimal`.

## Entorno

`VEHICLES_SERVICE_URL`, `MAINTENANCE_SERVICE_URL`, `INTERNAL_API_KEY` (clave compartida para las llamadas internas). El servicio expone el puerto interno `8003` y se inicia mediante `docker compose up -d --build` desde la raíz.

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

No expongas este servicio directamente a Internet: está previsto para comunicación entre contenedores y para consumo autorizado mediante el Gateway.
