# Cómo contribuir

Gracias por querer mejorar Auditor DIAN. Esta guía cabe en cinco minutos de lectura.

## Por dónde empezar

- Las issues con la etiqueta [`good first issue`](https://github.com/RafaGM1108/auditor-dian-core/labels/good%20first%20issue) son cambios acotados, pensados para un primer aporte.
- El tablero [Auditor DIAN Core](https://github.com/users/RafaGM1108/projects/14) muestra qué está en curso.
- Para preguntas o ideas usa [Discussions](https://github.com/RafaGM1108/auditor-dian-core/discussions). Las issues son para defectos y tareas concretas.
- Antes de un cambio grande, comenta en la issue cómo piensas hacerlo. Así nadie trabaja dos veces en lo mismo.

## Preparar el entorno

Requiere [uv](https://docs.astral.sh/uv/) y Python 3.11 o superior.

```bash
uv sync
uv run pytest --cov=auditor_dian --cov-fail-under=100
uv run ruff check . && uv run ruff format --check .
```

`SPEC.md` es la fuente de verdad del alcance; léelo antes de cambiar comportamiento.

## Reglas del proyecto

- **Nunca subas facturas reales**, ni en pruebas, ni en issues, ni en capturas. Los fixtures son sintéticos: NIT, nombres y CUFE inventados. Puedes copiar uno de `tests/fixtures/` y cambiarle los valores.
- **El modelo nunca calcula cifras**: toda cifra sale de SQL o de código con pruebas.
- **Montos exactos**: `Decimal` en Python y `DECIMAL` en DuckDB. Nunca `float`.
- **Sin llamadas de red** en el código: las facturas no salen del equipo.
- **Nada de inventar campos ni códigos DIAN**: si algo no está claro, verifícalo en el Anexo Técnico vigente y deja la referencia en un comentario.
- **Cobertura del 100 %**: la CI la exige en cada cambio. Escribe primero la prueba que falla.
- **Español** en documentación, comentarios, mensajes de commit y nombres del dominio (`documentos`, `retenciones`). Los términos técnicos genéricos pueden ir en inglés.

## Documentación que acompaña el cambio

Si no quedó escrito en `docs/`, no pasó:

1. Una entrada en `docs/bitacora.md`: qué se hizo, qué se aprendió y qué problemas hubo.
2. Si tomaste una decisión de diseño, una nota en `docs/decisiones/NNNN-titulo.md` con contexto, decisión, alternativas descartadas y consecuencias.
3. Si cambia el alcance, actualiza `SPEC.md`.
4. Si cambias una herramienta MCP, actualiza también `mcpb/manifest.json`. Una prueba revisa que coincidan.

## Commits y pull requests

- Mensajes en español y en imperativo: `Agrega lector de documento soporte`.
- Un pull request por tema, con `Closes #N` en la descripción.
- Explica cómo lo probaste. La plantilla trae la lista de chequeo.

## Seguridad

Si encuentras una vulnerabilidad, **no abras una issue pública**: sigue [SECURITY.md](SECURITY.md).

## Conducta

Este proyecto sigue un [código de conducta](CODE_OF_CONDUCT.md). Al participar, aceptas respetarlo.
