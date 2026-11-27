Cierra #

## Qué cambia

<!-- En dos o tres líneas: qué hace y por qué. -->

## Cómo se probó

<!-- Qué pruebas agregaste y si fallaban antes del cambio. -->

## Lista de chequeo

- [ ] `uv run pytest --cov=auditor_dian --cov-fail-under=100` pasa.
- [ ] `uv run ruff check .` y `uv run ruff format --check .` pasan.
- [ ] Sin datos reales: los fixtures son sintéticos.
- [ ] Entrada en `docs/bitacora.md`.
- [ ] Decisión en `docs/decisiones/`, si hubo una de diseño.
- [ ] `SPEC.md` y `mcpb/manifest.json` al día, si cambia el alcance o una herramienta MCP.
