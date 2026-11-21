# 0009 — Licencia MIT y nombre público

Fecha: 2026-11-20

## Contexto

SPEC §14 dejaba para antes de publicar dos decisiones: la licencia (MIT o AGPL-3.0) y el nombre público. `pro` es un plugin aparte (decisión 0008), así que su licencia no depende de la de `core`.

## Decisión

- **Licencia MIT** (`LICENSE`, y `license = "MIT"` en `pyproject.toml`).
- **Nombre público: Auditor DIAN.** Menciona la DIAN, como pidió el equipo, y coincide con el código: el paquete sigue siendo `auditor-dian-core`, el comando `auditor` y el servidor MCP `auditor-dian`. No hubo que renombrar nada.
- **Aclaración en el README**: no es un producto oficial de la DIAN ni está afiliado a ella; "DIAN" solo describe las facturas que procesa.
- **Logo propio** (`src/auditor_dian/logo.svg`, movido desde `docs/` para que viaje en el paquete; `logo.png` es la misma imagen a 256 px): una factura bajo una lupa con un visto, en verde azulado y ámbar. No usa el escudo, el nombre gráfico ni los colores de la DIAN.

## Alternativas descartadas

- **AGPL-3.0**: protege contra competidores que lo ofrezcan como servicio sin publicar cambios, pero desanima a empresas y a integradores contables, y obligaría a pedir un acuerdo de cesión (CLA) a quien contribuya para poder usar sus aportes en `pro`.
- **Un nombre sin la sigla DIAN**: evita cualquier confusión, pero el equipo quiere que el nombre diga para qué sirve; la aclaración del README cubre el riesgo.

## Consecuencias

- Cualquiera puede usar, modificar y redistribuir `core`, también dentro de software cerrado, conservando el aviso de copyright.
- Si la DIAN objetara el uso de su sigla, cambiar el nombre público solo afecta el README y el logo; el nombre del paquete es técnico.
