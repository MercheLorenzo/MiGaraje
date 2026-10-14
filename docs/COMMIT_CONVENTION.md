# Convención de commits semánticos

## Objetivo

Utilizar mensajes de commit claros y consistentes para facilitar la lectura del historial de Git y la identificación de los cambios realizados en MiGaraje.

## Formato

```bash
git commit -m "tipo: descripción breve del cambio"
```

Ejemplo:

```bash
git commit -m "feat: add vehicle registration endpoint"
```

## Prefijos

| Prefijo | Uso | Ejemplo |
|---|---|---|
| `feat:` | Añadir una funcionalidad nueva. | `feat: add vehicle registration` |
| `fix:` | Corregir un error. | `fix: validate vehicle year` |
| `docs:` | Modificar documentación. | `docs: update cloud architecture diagram` |
| `refactor:` | Mejorar la estructura del código sin cambiar su comportamiento externo. | `refactor: simplify vehicle validation` |
| `test:` | Añadir o modificar pruebas. | `test: add vehicle registration tests` |
| `style:` | Cambiar el formato del código sin alterar su lógica. | `style: format vehicle service code` |
| `chore:` | Realizar tareas generales de mantenimiento. | `chore: update project dependencies` |
| `perf:` | Mejorar el rendimiento. | `perf: optimize database queries` |
| `build:` | Modificar la construcción o las dependencias. | `build: update Docker configuration` |
| `ci:` | Modificar la integración o automatización continua. | `ci: add automated test workflow` |

## Reglas de uso

1. Cada commit debe representar un cambio coherente.
2. Las descripciones se escribirán preferentemente en inglés y comenzarán con un verbo en imperativo, como `add`, `fix`, `update` o `remove`.
3. Los mensajes deben ser breves, específicos y descriptivos.
4. Se elegirá el prefijo según la naturaleza del cambio.
5. Cuando corresponda, se relacionará el commit con una Issue de GitHub.

Ejemplo con una Issue:

```bash
git commit -m "feat: add vehicle registration (#12)"
```

El número debe corresponder a una Issue real del repositorio.

## Ejemplos para MiGaraje

```bash
git commit -m "feat: add maintenance history endpoint"
git commit -m "fix: reject invalid vehicle years"
git commit -m "docs: update project README"
git commit -m "test: add vehicle registration tests"
git commit -m "refactor: separate vehicle business logic"
```

## Resumen rápido

- `feat:` — nueva funcionalidad.
- `fix:` — corrección de errores.
- `docs:` — documentación.
- `refactor:` — reorganización del código.
- `test:` — pruebas.
- `style:` — formato del código.
- `chore:` — mantenimiento general.
- `perf:` — rendimiento.
- `build:` — construcción y dependencias.
- `ci:` — integración continua.

**Aplicación:** esta convención se utilizará en los commits del repositorio MiGaraje para mantener un historial uniforme y comprensible.
