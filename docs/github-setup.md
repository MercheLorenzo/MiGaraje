# Configuración de GitHub para el Hito 1

Esta guía sirve como lista de comprobación. Los elementos de GitHub Projects, milestones e Issues se crean en la interfaz web; los archivos de plantilla se versionan en el repositorio.

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

## 2. Milestones sugeridos

1. `Hito 1 - Definición y arquitectura`
2. `Hito 2 - Servicios y persistencia`
3. `Hito 3 - Contenerización y despliegue`
4. `Hito 4 - Pruebas, observabilidad y entrega`

Ajusta los nombres y fechas a los hitos reales de la asignatura.

## 3. Etiquetas sugeridas

- `user-story` — historia de usuario.
- `architecture` — arquitectura y diseño.
- `backend` — API o lógica de backend.
- `database` — persistencia.
- `devops` — contenedores, CI/CD o despliegue.
- `documentation` — documentación.
- `testing` — pruebas.
- `security` — seguridad y privacidad.
- `bug` — comportamiento incorrecto.
- `enhancement` — mejora funcional.

La plantilla de historias añade automáticamente `user-story`; crea esa etiqueta en GitHub si aún no existe.

## 4. Historias iniciales sugeridas

Crear cada historia como un GitHub Issue usando la plantilla `.github/ISSUE_TEMPLATE/user_story.md`.

1. **Registrar un vehículo:** Como propietario, quiero registrar un vehículo para centralizar sus datos.
2. **Consultar el historial:** Como propietario, quiero registrar y consultar reparaciones para recordar qué se hizo y qué piezas se utilizaron.
3. **Configurar mantenimiento:** Como propietario, quiero definir intervalos por fecha y kilometraje para conocer cuándo corresponde una revisión.
4. **Detectar vencimientos:** Como propietario, quiero ver tareas próximas o vencidas para priorizar el mantenimiento.
5. **Recibir recordatorios:** Como propietario, quiero recibir avisos anticipados para no olvidar las tareas.
6. **Consultar gastos:** Como propietario, quiero consultar gastos por vehículo y período para controlar el coste de mantenimiento.
7. **Desplegar servicios en contenedores:** Como desarrollador, quiero ejecutar los componentes en contenedores para disponer de un entorno reproducible.
8. **Monitorizar la aplicación:** Como responsable técnico, quiero consultar logs y métricas para detectar errores operativos.

Cada Issue debe tener criterios de aceptación verificables, checklist técnico, etiqueta `user-story` y el milestone correspondiente.

## 5. GitHub Projects

Crear un proyecto vinculado al repositorio y añadir los Issues como elementos del backlog. Se recomienda una vista de tablero agrupada por estado y una vista de tabla agrupada por milestone. Campos útiles: `Status` (Todo, In progress, In review, Done), `Priority` y `Milestone`.

## 6. Reglas de integración

Si el plan de GitHub y los permisos del repositorio lo permiten, proteger `main` para requerir Pull Request y comprobaciones antes de integrar. En un repositorio individual, una revisión formal puede ser una auto-revisión documentada si no hay otra persona revisora.
