# Configuración de GitHub para el Hito 1

Los elementos de GitHub Projects, milestones e Issues se crean en la interfaz web; los archivos de plantilla se versionan en el repositorio.

## 1. Estrategia de ramas

- `main`: versión estable.
- `feature/<descripcion-corta>`: nuevas funcionalidades.
- `fix/<descripcion-corta>`: correcciones.
- Integrar cambios mediante Pull Requests.
- Usar commits semánticos: `feat:`, `fix:`, `docs:`, `test:`, `refactor:` y `chore:`.

Ejemplos:
- `docs: add initial cloud architecture`
- `feat: register vehicle endpoint`
- `test: cover maintenance due-date calculation`

## 2. Milestones

1. `M1 - Diseño y configuración`
2. `M2 - Gestión de vehículos`
3. `M3 - Mantenimiento y gastos`
4. `M4 - Notificaciones, estadísticas y despliegue`

Estos son los milestones creados de momento. Se irán añadiendo más conforme se avance en el proyecto.

## 3. Etiquetas

- `architecture` — Arquitectura y diseño.
- `backend` — API y lógica de negocio.
- `bug` — Errores que hay que corregir.
- `cloud` — Docker, infraestructura y despliegue cloud.
- `database` — Persistencia y modelo de datos.
- `documentation` — README, diagramas y documentación.
- `enhancement` — Mejoras de funcionalidades existentes.
- `priority: high` — Trabajo de prioridad alta.
- `priority: low` — Trabajo de prioridad baja.
- `priority: medium` — Trabajo de prioridad media.
- `task` — Tareas técnicas o de configuración.
- `testing` — Pruebas y validación.
- `user-story` — Historia de usuario funcionales.
- `security` — Seguridad y privacidad.

La plantilla de historias añade automáticamente `user-story`.

## 4. Historias de usuario (Issues) iniciales

Crear cada historia como un GitHub Issue usando la plantilla `.github/ISSUE_TEMPLATE/user_story.md`.

1. **Registrar un vehículo:** Como usuario de MiGaraje, quiero registrar mis vehículos con sus datos principales, para mantener organizada su información en un único lugar.
2. **Consultar los vehículos registrados:** Como usuario de MiGaraje, quiero consultar la lista de mis vehículos registrados y ver sus datos principales, para localizar rápidamente el vehículo que deseo gestionar.
3. **Editar y eliminar un vehículo:** Como usuario de MiGaraje, quiero modificar los datos de mis vehículos y eliminar aquellos que ya no deseo gestionar, para mantener mi inventario actualizado.
4. **Registrar reparaciones y mantenimientos:** Como usuario de MiGaraje, quiero registrar las reparaciones y operaciones de mantenimiento realizadas en mis vehículos, para conservar un registro detallado de las intervenciones y sus costes.
5. **Consultar el historial de un vehículo:** Como usuario de MiGaraje, quiero consultar el historial de reparaciones y mantenimientos de cada vehículo, para conocer las intervenciones realizadas y su evolución a lo largo del tiempo.
6. **Consultar los gastos de mantenimiento:** Como usuario de MiGaraje, quiero consultar los gastos asociados a las reparaciones y mantenimientos de mis vehículos, para controlar cuánto dinero destino a su conservación.
7. **Recibir recordatorios de mantenimiento:** Como usuario de MiGaraje, quiero configurar recordatorios de mantenimiento basados en fechas o kilometrajes, para realizar las revisiones a tiempo y evitar olvidos.
8. **Consultar estadísticas de gastos:** Como usuario de MiGaraje, quiero consultar estadísticas de los gastos de mantenimiento por vehículo, periodo y categoría, para identificar patrones de gasto y comparar los costes de conservación.
9. **Desplegar servicios en contenedores:** Como desarrollador, quiero ejecutar los componentes de MiGaraje en contenedores para disponer de un entorno reproducible y facilitar su despliegue.
10. **Monitorizar la aplicación:** Como responsable técnico, quiero consultar los registros (logs) y las métricas de MiGaraje para detectar errores operativos y evaluar el funcionamiento de los servicios.

Cada Issue debe tener criterios de aceptación verificables, checklist técnico, etiqueta `user-story` y el milestone correspondiente.

## 5. GitHub Projects

Creado un proyecto vinculado al repositorio en el cual se han añadidido los Issues (HU) como elementos del backlog. Campos útiles: `Status` (Todo, In progress, In review, Done).

## 6. Reglas de integración

Si el plan de GitHub y los permisos del repositorio lo permiten, proteger `main` para requerir Pull Request y comprobaciones antes de integrar. En un repositorio individual, una revisión formal puede ser una auto-revisión documentada si no hay otra persona revisora.
