# 0003 — `pytest-cov` para medir cobertura

Fecha: 2026-11-20

## Contexto

`CLAUDE.md` pide registrar la cobertura al cerrar cada hito, y el SPEC §3 exige justificar por escrito cada dependencia nueva.

## Decisión

Se agrega `pytest-cov` solo como dependencia de desarrollo (`[dependency-groups] dev`). Se usa al cerrar hitos: `uv run pytest --cov=auditor_dian --cov-report=term-missing`. No se agrega a la CI ni se fija un umbral mínimo.

## Alternativas descartadas

- **`coverage` directo**: `pytest-cov` lo usa por debajo y evita un comando extra.
- **Umbral en la CI**: con dos personas y hitos cortos, un umbral obligaría a escribir pruebas para alcanzar un número y no por el riesgo. Se revisará si la cobertura empieza a bajar.

## Consecuencias

- No llega nada nuevo a los usuarios de `core`: la dependencia es solo de desarrollo.
- La cifra es de líneas, no de ramas.
