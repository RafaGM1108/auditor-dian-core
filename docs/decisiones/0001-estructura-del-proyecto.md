# 0001 — Estructura del proyecto con `uv` y `src/`

Fecha: 2026-11-19

## Contexto

El SPEC fija Python 3.11+, `uv` como gestor y el esquema en `src/auditor_dian/schema.sql`. Hay que decidir el nombre del paquete, el backend de construcción y qué dependencias entran desde el inicio.

## Decisión

- Distribución `auditor-dian-core` (nombre del repositorio), módulo importable `auditor_dian` (el que usa el SPEC), en diseño `src/`.
- Backend de construcción `uv_build`, el que genera `uv init`.
- `.python-version` fijado en 3.11, el mínimo soportado, para no usar por accidente sintaxis de versiones más nuevas.
- Dependencias: solo las que el hito en curso necesita. Hoy `lxml` (parser, M1) y `typer` (CLI). `duckdb`, `openpyxl` y `mcp` se agregan en M2, M3 y M4. Desarrollo: `pytest` y `ruff`.
- Comando de consola `auditor`, como en el SPEC §9.

## Alternativas descartadas

- **Diseño plano (paquete en la raíz)**: con `src/` las pruebas corren contra el paquete instalado y no contra la carpeta, lo que detecta archivos que faltan en la distribución.
- **`hatchling` o `setuptools`**: funcionan igual para este caso; `uv_build` no requiere configuración adicional.
- **Instalar todo el stack desde el día uno**: agrega dependencias que no se usan durante semanas y oculta cuál hito introdujo cada una.

## Consecuencias

- El nombre de la distribución y el del módulo difieren; está documentado en `pyproject.toml` (`module-name`).
- Cada hito que agregue una dependencia del stack lo anota en la bitácora.
