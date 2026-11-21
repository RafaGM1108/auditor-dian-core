# 0002 — Grafo de conocimiento del repositorio versionado

Fecha: 2026-11-20

## Contexto

Las sesiones con asistentes de código releen SPEC, bitácora y código en cada tarea, lo que gasta tokens y tiempo. Somos dos personas trabajando en el mismo repositorio.

## Decisión

- Se genera un grafo de conocimiento con `graphify` (código por AST, documentos por extracción semántica) en `graphify-out/`.
- Se versionan `graph.json`, `GRAPH_REPORT.md`, `graph.html`, `manifest.json`, `cost.json` y `cache/`, para que la otra persona lo use y lo actualice de forma incremental sin volver a extraer todo.
- No se versionan `.graphify_python` ni `.graphify_root`, que contienen rutas absolutas de cada máquina.
- `CLAUDE.md` indica consultar el grafo antes de explorar y actualizarlo tras cambios.

## Alternativas descartadas

- **No versionar el grafo**: cada persona tendría que regenerarlo, y la parte semántica cuesta tokens.
- **Hook post-commit de actualización automática**: dejaría el grafo modificado y sin commit después de cada commit. Se prefiere actualizarlo a mano dentro del mismo commit.

## Consecuencias

- El grafo puede quedar desactualizado si se olvida regenerarlo. `GRAPH_REPORT.md` no es una fuente de verdad: lo es el código y `SPEC.md`.
- Los nodos inferidos (INFERRED) por el modelo deben verificarse antes de basar una decisión en ellos.
- El grafo no contiene datos de clientes: solo se extrae código, SPEC y `docs/` (los XML de `tests/fixtures/` no se procesan).
