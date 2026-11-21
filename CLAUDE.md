# CLAUDE.md — auditor-dian-core

Lee `SPEC.md` antes de cualquier tarea. Es la fuente de verdad del alcance.

## Reglas del proyecto

- Idioma: documentación, mensajes de commit, comentarios y nombres de dominio en español (`documentos`, `retenciones`). Nombres técnicos genéricos pueden ir en inglés.
- El modelo nunca calcula cifras: toda cifra sale de SQL o código probado.
- Montos como `Decimal` en Python. En DuckDB, montos, precios, cantidades y TRM en `DECIMAL(21,6)` y tarifas en `DECIMAL(9,3)`, exactos como vienen en el XML; se redondea a 2 decimales solo al presentar (decisión 0004). Nunca `float`.
- Sin llamadas de red en el código de `core`.
- `core` nunca importa nada de `pro`.
- Nunca subir datos reales. Fixtures solo sintéticos o anonimizados.
- Si un campo DIAN no está claro, verificar contra el Anexo Técnico vigente y dejar la referencia en un comentario; no inventar XPaths ni códigos.
- Cambios pequeños, un hito a la vez, con pruebas.

## Comandos

```
uv sync
uv run pytest
uv run ruff check .
uv run auditor --help
```

## Documentación continua (obligatoria)

Al terminar cada tarea o sesión de trabajo:

1. Añadir una entrada en `docs/bitacora.md`: fecha, qué se hizo, qué se aprendió, problemas encontrados.
2. Si se tomó una decisión de diseño (librería, esquema, estructura), crear `docs/decisiones/NNNN-titulo.md` con: contexto, decisión, alternativas descartadas, consecuencias.
3. Si cambia el alcance, actualizar `SPEC.md` y anotarlo en la bitácora.
4. Al cerrar un hito, marcarlo en `docs/cronograma.md` y escribir un resumen de 5–10 líneas en `docs/hitos/MN.md` con métricas (documentos probados, pruebas, cobertura).

Estos archivos alimentan el informe final (`docs/informe/informe.tex`, formato IEEE), así que deben escribirse en lenguaje claro para alguien externo.

## Commits

Mensajes en español, en imperativo: `Agrega parser de AttachedDocument`.

## Mapa del código (grafo de conocimiento)

`graphify-out/` contiene un grafo del repositorio (código + `docs/` + SPEC). Úsalo para no releer archivos completos:

1. Antes de explorar, lee `graphify-out/GRAPH_REPORT.md` (nodos centrales, comunidades, conexiones).
2. Para preguntas puntuales: `graphify query "<pregunta>"`, `graphify explain "<nodo>"` o `graphify path "<A>" "<B>"`. Abre solo los archivos que el grafo señale.
3. Tras cambiar código, actualizar sin costo de tokens (solo AST): `graphify update .`. Si cambiaron documentos, regenerar con `/graphify . --update` y subir `graphify-out/` en el mismo commit.
